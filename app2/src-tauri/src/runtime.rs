use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::{
    io::{BufRead, BufReader, Read, Write},
    path::PathBuf,
    process::{Command, Stdio},
    thread,
};
use tauri::{ipc::Channel, Manager};

#[derive(Clone, Deserialize)]
pub struct RuntimeOptions {
    python: String,
    directory: String,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
pub struct Environment {
    python: String,
    directory: String,
    app_version: String,
}

#[derive(Clone, Serialize)]
pub struct OutputLine {
    stream: &'static str,
    text: String,
}

#[derive(Serialize)]
pub struct BridgeResult {
    data: Value,
    warnings: String,
}

#[tauri::command]
pub fn environment(app: tauri::AppHandle) -> Result<Environment, String> {
    let local = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../../pacev2/.venv")
        .join(if cfg!(windows) {
            "Scripts/python.exe"
        } else {
            "bin/python"
        });
    Ok(Environment {
        python: if cfg!(debug_assertions) && local.is_file() {
            local.to_string_lossy().into_owned()
        } else if cfg!(windows) {
            "python".into()
        } else {
            "python3".into()
        },
        directory: app
            .path()
            .home_dir()
            .map_err(|e| e.to_string())?
            .to_string_lossy()
            .into_owned(),
        app_version: app.package_info().version.to_string(),
    })
}

fn command(options: &RuntimeOptions) -> Result<Command, String> {
    if options.python.trim().is_empty() {
        return Err("Choose the Python executable containing pacev2 in Settings.".into());
    }
    if !PathBuf::from(&options.directory).is_dir() {
        return Err(format!(
            "Working directory does not exist: {}",
            options.directory
        ));
    }
    let mut command = Command::new(&options.python);
    command
        .current_dir(&options.directory)
        .env("PYTHONUNBUFFERED", "1")
        .env("PYTHONIOENCODING", "utf-8")
        .env("NO_COLOR", "1")
        .env("TERM", "dumb")
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());
    #[cfg(windows)]
    {
        use std::os::windows::process::CommandExt;
        command.creation_flags(0x08000000);
    }
    Ok(command)
}

#[tauri::command]
pub async fn bridge(options: RuntimeOptions, request: Value) -> Result<BridgeResult, String> {
    tauri::async_runtime::spawn_blocking(move || {
        let mut child = command(&options)?
            .args(["-c", include_str!("../bridge.py")])
            .stdin(Stdio::piped())
            .spawn()
            .map_err(|e| format!("Could not start {}: {e}", options.python))?;
        let input = serde_json::to_vec(&request).map_err(|e| e.to_string())?;
        // Write concurrently: a failed Python import can exit before consuming stdin.
        let mut stdin = child.stdin.take().ok_or("Python stdin is unavailable")?;
        let writer = thread::spawn(move || stdin.write_all(&input));
        let output = child.wait_with_output().map_err(|e| e.to_string())?;
        let written = writer
            .join()
            .map_err(|_| "Request writer stopped unexpectedly")?;
        let stderr = String::from_utf8_lossy(&output.stderr).trim().to_owned();
        if !output.status.success() {
            return Err(if stderr.is_empty() {
                format!(
                    "Python exited with {}. Check the runtime in Settings.",
                    output.status
                )
            } else {
                stderr
            });
        }
        written.map_err(|e| format!("Could not send the request to Python: {e}"))?;
        Ok(BridgeResult {
            data: serde_json::from_slice(&output.stdout)
                .map_err(|e| format!("Invalid response from pacev2: {e}"))?,
            warnings: stderr,
        })
    })
    .await
    .map_err(|e| e.to_string())?
}

fn forward(
    reader: impl Read,
    stream: &'static str,
    channel: Channel<OutputLine>,
) -> Result<(), String> {
    for line in BufReader::new(reader).lines() {
        let text = line.map_err(|e| format!("Could not read {stream}: {e}"))?;
        channel
            .send(OutputLine { stream, text })
            .map_err(|e| format!("Could not deliver command output: {e}"))?;
    }
    Ok(())
}

#[tauri::command]
pub async fn run_pace(
    options: RuntimeOptions,
    args: Vec<String>,
    output: Channel<OutputLine>,
) -> Result<i32, String> {
    tauri::async_runtime::spawn_blocking(move || {
        let mut child = command(&options)?
            .args(["-m", "pacev2"])
            .args(args)
            .stdin(Stdio::null())
            .spawn()
            .map_err(|e| format!("Could not start {}: {e}", options.python))?;
        let stdout = child.stdout.take().ok_or("Command stdout is unavailable")?;
        let stderr = child.stderr.take().ok_or("Command stderr is unavailable")?;
        let errors = output.clone();
        let out = thread::spawn(move || forward(stdout, "stdout", output));
        let err = thread::spawn(move || forward(stderr, "stderr", errors));
        let status = child.wait().map_err(|e| e.to_string())?;
        out.join()
            .map_err(|_| "Output reader stopped unexpectedly")??;
        err.join()
            .map_err(|_| "Error reader stopped unexpectedly")??;
        status
            .code()
            .ok_or("Command was terminated before returning an exit code".into())
    })
    .await
    .map_err(|e| e.to_string())?
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;
    use std::sync::{Arc, Mutex};

    fn options() -> RuntimeOptions {
        RuntimeOptions {
            python: PathBuf::from(env!("CARGO_MANIFEST_DIR"))
                .join("../../pacev2/.venv")
                .join(if cfg!(windows) {
                    "Scripts/python.exe"
                } else {
                    "bin/python"
                })
                .to_string_lossy()
                .into_owned(),
            directory: env!("CARGO_MANIFEST_DIR").into(),
        }
    }

    #[test]
    fn embedded_adapter_validates_without_touching_history() {
        let result = tauri::async_runtime::block_on(bridge(
            options(),
            json!({"action": "validate", "content": "projects = []"}),
        ))
        .expect("pacev2 must be installed in its development venv");
        assert_eq!(result.data["projects"], json!([]));
    }

    #[test]
    fn embedded_adapter_returns_python_errors() {
        let result = tauri::async_runtime::block_on(bridge(
            options(),
            json!({"action": "validate", "content": "projects = ["}),
        ));
        assert!(result.is_err());
    }

    #[test]
    fn native_runner_streams_real_cli_output() {
        let messages = Arc::new(Mutex::new(Vec::new()));
        let received = messages.clone();
        let channel = Channel::new(move |message| {
            received.lock().unwrap().push(message);
            Ok(())
        });
        let code =
            tauri::async_runtime::block_on(run_pace(options(), vec!["--version".into()], channel))
                .unwrap();
        assert_eq!(code, 0);
        assert!(!messages.lock().unwrap().is_empty());
    }

    #[test]
    fn invalid_runtime_is_an_error_not_a_successful_empty_result() {
        let mut invalid = options();
        invalid.python.clear();
        assert!(command(&invalid).is_err());
        let mut missing = options();
        missing.directory = "/a/nonexistent/pace/workspace".into();
        assert!(command(&missing).is_err());
    }
}
