export function parseArguments(input: string): string[] {
    const args: string[] = [];
    let value = "",
        quote = "",
        started = false;
    for (let i = 0; i < input.length; i++) {
        const char = input[i];
        if (
            char === "\\" &&
            quote !== "'" &&
            i + 1 < input.length &&
            (input[i + 1] === quote ||
                input[i + 1] === "\\" ||
                (!quote && /[\s"']/.test(input[i + 1])))
        ) {
            value += input[++i];
            started = true;
        } else if (quote) {
            if (char === quote) quote = "";
            else value += char;
        } else if (char === '"' || char === "'") {
            quote = char;
            started = true;
        } else if (/\s/.test(char)) {
            if (started) args.push(value);
            value = "";
            started = false;
        } else {
            value += char;
            started = true;
        }
    }
    if (quote)
        throw new Error(
            "Close the quoted argument before running the command.",
        );
    if (started) args.push(value);
    return args;
}

export function commandPreview(args: string[]): string {
    return [
        "pacev2",
        ...args.map((arg) =>
            /^[\w./:=+-]+$/.test(arg) ? arg : JSON.stringify(arg),
        ),
    ].join(" ");
}

export function scopedArgs(
    path: string,
    from: string,
    to: string,
    args: string[],
): string[] {
    return [
        "-C",
        path,
        ...(from ? ["--from", from] : []),
        ...(to ? ["--to", to] : []),
        ...args,
    ];
}

export function cleanOutput(text: string): string {
    return text.replace(/\x1b\[[0-?]*[ -/]*[@-~]/g, "").replace(/\r/g, "");
}
