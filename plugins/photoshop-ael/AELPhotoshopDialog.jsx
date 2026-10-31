/*
MIT License
Copyright (c) 2026 Pere Guerra Serra
Processed with Agentic Eclipse Library by Pere Guerra —
https://github.com/PeterWar/Agentic-Eclipse-Library
*/

// Two choices only: the RAW files of the totality and, if there are any, the calibration frames, plus where the result
// goes. Everything else (camera, levels, the Moon, the registration on the Sun, colour, filters) AEL measures.
var AELPhotoshopDialog = function () {
    var RAW = /\.(cr2|cr3|nef|arw|dng|raf|orf|rw2)$/i;
    var win = new Window("dialog", "Agentic Eclipse Library");
    win.orientation = "column";
    win.alignChildren = "fill";
    win.spacing = 12;
    win.margins = 18;

    var intro = win.add("statictext", undefined,
        "Choose the RAW photos of the totality. AEL stacks them into one image with its filter layers " +
        "and opens it here.", {multiline: true});
    intro.preferredSize = [460, 34];

    function picker(label, empty, action) {
        var group = win.add("group");
        group.alignChildren = ["left", "center"];
        var caption = group.add("statictext", undefined, label);
        caption.preferredSize.width = 170;
        var button = group.add("button", undefined, action);
        var status = group.add("statictext", undefined, empty);
        status.preferredSize.width = 170;
        return {button: button, status: status, files: [], empty: empty};
    }
    function choose(target, prompt) {
        var chosen = File.openDialog(prompt, function (f) { return f instanceof Folder || RAW.test(f.name); }, true);
        if (!chosen) return;
        if (!(chosen instanceof Array)) chosen = [chosen];
        var keep = [], i;
        for (i = 0; i < chosen.length; i++) if (RAW.test(chosen[i].name)) keep.push(chosen[i].fsName);
        target.files = keep;
        target.status.text = keep.length ? keep.length + (keep.length === 1 ? " file" : " files") : target.empty;
    }
    // The folder as a person reads it: from the home folder, and its end when it is long.
    function shown(folder) {
        var home = Folder("~").fsName, path = folder.fsName;
        if (path.indexOf(home + "/") === 0) path = "~" + path.substring(home.length);
        return path.length > 30 ? "…" + path.substring(path.length - 29) : path;
    }

    var raws = picker("Totality RAW photos", "none chosen", "Choose…");
    raws.button.onClick = function () { choose(raws, "RAW photos of the totality (select them all)"); };
    var calibration = picker("Darks and flats (optional)", "none", "Choose…");
    calibration.button.onClick = function () { choose(calibration, "Dark and flat frames of the same camera"); };
    // Each run makes a new folder, named with its date and time, inside this one.
    var output = picker("Output folder", "", "Browse…");
    output.folder = AELPhotoshop.defaultOutput();
    output.status.text = shown(output.folder);
    output.status.helpTip = output.folder.fsName;
    output.button.onClick = function () {
        var chosen = output.folder.selectDlg("Folder for the results (a new folder is made inside it for each run)");
        if (!chosen) return;
        output.folder = chosen;
        output.status.text = shown(chosen);
        output.status.helpTip = chosen.fsName;
    };

    var buttons = win.add("group");
    buttons.alignment = "right";
    var cancel = buttons.add("button", undefined, "Cancel", {name: "cancel"});
    var run = buttons.add("button", undefined, "Make the image", {name: "ok"});
    var answer = null;
    run.onClick = function () {
        if (!raws.files.length) {
            alert("Choose the RAW photos of the totality first.");
            return;
        }
        AELPhotoshop.saveOutput(output.folder.fsName);
        answer = {raw: raws.files, calibration: calibration.files, output: output.folder.fsName};
        win.close(1);
    };
    cancel.onClick = function () { win.close(0); };
    if (win.show() !== 1) return null;
    return answer;
};
