/*
MIT License
Copyright (c) 2026 Pere Guerra Serra
Processed with Agentic Eclipse Library by Pere Guerra —
https://github.com/PeterWar/Agentic-Eclipse-Library
*/

var AELPhotoshopDialog = function () {
    var win = new Window("dialog", "Agentic Eclipse Library — Photoshop");
    win.orientation = "column";
    win.alignChildren = "fill";
    win.spacing = 10;
    win.margins = 16;

    function row(label, value, browse) {
        var group = win.add("group");
        group.alignChildren = ["left", "center"];
        var caption = group.add("statictext", undefined, label);
        caption.preferredSize.width = 145;
        var field = group.add("edittext", undefined, value || "");
        field.preferredSize.width = 440;
        if (browse) {
            var button = group.add("button", undefined, "Browse…");
            button.onClick = function () { browse(field); };
        }
        return field;
    }
    function folder(field) {
        var chosen = Folder.selectDialog("Choose a folder", field.text ? new Folder(field.text) : undefined);
        if (chosen) field.text = chosen.fsName;
    }
    function file(field, prompt) {
        var chosen = File.openDialog(prompt);
        if (chosen) field.text = chosen.fsName;
    }

    var operationGroup = win.add("group");
    operationGroup.add("statictext", undefined, "Operation");
    var operation = operationGroup.add("dropdownlist", undefined, [
        "structure — active document", "polar — active document",
        "master — linear master and filters", "filters — from linear.npy"]);
    operation.selection = 0;
    operation.preferredSize.width = 410;

    var output = row("Output parent", Folder.myDocuments.fsName, folder);
    var geometry = row("Geometry JSON", "", function (field) { file(field, "EclipseGeometry JSON"); });
    var python = row("Python (optional)", "", function (field) { file(field, "Python 3.10+ executable"); });
    var ael = row("AEL folder (optional)", "", folder);
    var linear = row("linear.npy (filters)", "", function (field) { file(field, "Existing linear.npy"); });
    var camera = row("Camera profile (master)", "", function (field) { file(field, "Measured camera profile JSON"); });
    var valid = row("Valid mask (structure)", "", function (field) { file(field, "Optional boolean valid.npy"); });
    var rmax = row("Outer radius (polar)", "4.0");
    var frames = [];
    var frameGroup = win.add("group");
    var frameButton = frameGroup.add("button", undefined, "Choose master frames…");
    var frameLabel = frameGroup.add("statictext", undefined, "No frames selected");
    frameButton.onClick = function () {
        var chosen = File.openDialog("Linear RGB or RAW frames; one camera and ISO", undefined, true);
        if (chosen) {
            frames = chosen;
            frameLabel.text = frames.length + " frame(s)";
        }
    };

    var note = win.add("statictext", undefined,
        "The source is never edited. Results open as new documents and previous runs are not overwritten.", {multiline: true});
    note.preferredSize.width = 610;
    var buttons = win.add("group");
    buttons.alignment = "right";
    var cancel = buttons.add("button", undefined, "Cancel", {name: "cancel"});
    var run = buttons.add("button", undefined, "Run AEL", {name: "ok"});

    var answer = null;
    run.onClick = function () {
        var operations = ["structure", "polar", "master", "filters"];
        answer = {operation: operations[operation.selection.index], outputParent: output.text,
            geometry: geometry.text, python: python.text, aelFolder: ael.text,
            input: linear.text, camera: camera.text, valid: valid.text,
            rmax: parseFloat(rmax.text), frames: []};
        for (var i = 0; i < frames.length; i++) answer.frames.push(frames[i].fsName);
        win.close(1);
    };
    cancel.onClick = function () { win.close(0); };
    if (win.show() !== 1) return null;
    return answer;
};
