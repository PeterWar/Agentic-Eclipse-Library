/*
MIT License
Copyright (c) 2026 Pere Guerra Serra
Processed with Agentic Eclipse Library by Pere Guerra —
https://github.com/PeterWar/Agentic-Eclipse-Library
*/

// Two choices only: the RAW files of the totality and, if there are any, the calibration frames. Everything else
// (camera, levels, the Moon, the registration on the Sun, colour, filters, where the result goes) AEL measures.
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

    function picker(label, empty) {
        var group = win.add("group");
        group.alignChildren = ["left", "center"];
        var caption = group.add("statictext", undefined, label);
        caption.preferredSize.width = 170;
        var button = group.add("button", undefined, "Choose…");
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

    var raws = picker("Totality RAW photos", "none chosen");
    raws.button.onClick = function () { choose(raws, "RAW photos of the totality (select them all)"); };
    var calibration = picker("Darks and flats (optional)", "none");
    calibration.button.onClick = function () { choose(calibration, "Dark and flat frames of the same camera"); };

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
        answer = {raw: raws.files, calibration: calibration.files};
        win.close(1);
    };
    cancel.onClick = function () { win.close(0); };
    if (win.show() !== 1) return null;
    return answer;
};
