// Copyright (c) 2026

using System;
using System.IO;
using System.Text;
using System.Text.Json;
using Microsoft.Build.Framework;

namespace Pace;

public sealed class MonitorLogger : ILogger
{
    private StreamWriter writer;
    private readonly object gate = new();
    public LoggerVerbosity Verbosity { get; set; }
    public string Parameters { get; set; }

    public void Initialize(IEventSource source)
    {
        var path = Environment.GetEnvironmentVariable("PACE_MONITOR_EVENTS");
        if (string.IsNullOrEmpty(path))
            throw new LoggerException("PACE_MONITOR_EVENTS is not set.");
        writer = new StreamWriter(
            new FileStream(path, FileMode.Append, FileAccess.Write, FileShare.ReadWrite),
            new UTF8Encoding(false)) { AutoFlush = true };
        Write("ready", null, null, null, null);
        source.ProjectStarted += (_, e) =>
            Write("project_started", e.ProjectFile, null, null, e.BuildEventContext);
        source.ProjectFinished += (_, e) =>
            Write("project_finished", e.ProjectFile, null, e.Succeeded, e.BuildEventContext);
        source.TargetStarted += (_, e) =>
        {
            if (Stage(e.TargetName) is string stage)
                Write("stage_started", e.ProjectFile, stage, null, e.BuildEventContext);
        };
        source.TargetFinished += (_, e) =>
        {
            if (Stage(e.TargetName) is string stage)
                Write("stage_finished", e.ProjectFile, stage, e.Succeeded, e.BuildEventContext);
        };
    }

    private static string Stage(string target) => target switch
    {
        "Restore" => "restore",
        "CoreCompile" => "compile",
        "Build" => "build",
        "Publish" => "publish",
        "VSTest" => "test",
        _ => null
    };

    private void Write(string kind, string project, string stage, bool? succeeded, BuildEventContext context)
    {
        lock (gate)
            writer.WriteLine(JsonSerializer.Serialize(new
            {
                kind,
                project,
                stage,
                succeeded,
                context = context == null ? "" : $"{context.NodeId}:{context.ProjectContextId}:{context.TargetId}"
            }));
    }

    public void Shutdown()
    {
        lock (gate)
            writer?.Dispose();
    }
}
