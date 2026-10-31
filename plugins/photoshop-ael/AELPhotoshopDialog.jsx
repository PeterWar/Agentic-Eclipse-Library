/*
MIT License
Copyright (c) 2026 Pere Guerra Serra
Processed with Agentic Eclipse Library by Pere Guerra —
https://github.com/PeterWar/Agentic-Eclipse-Library
*/

// The RAW files of the totality and, if there are any, the darks and the flats, plus where the result goes. Everything
// else (camera, levels, the Moon, the registration on the Sun, colour) AEL measures; the filter layers are AEL's three
// default ones unless the advanced settings choose others. Every field and button says what it does when the pointer
// rests on it, with the words of the PixInsight connector.
var AELPhotoshopDialog = function () {
    var RAW = /\.(cr2|cr3|nef|arw|dng|raf|orf|rw2)$/i;
    var win = new Window("dialog", "Agentic Eclipse Library");
    win.orientation = "column";
    win.alignChildren = "fill";
    win.spacing = 12;
    win.margins = 18;

    var intro = win.add("statictext", undefined,
        "Choose the RAW photos of the totality. AEL stacks them into one image with its filter layers " +
        "and opens it here. AEL finds the Moon and the Sun by itself; your files are not changed.", {multiline: true});
    intro.preferredSize = [460, 50];

    function picker(label, empty, action, tip) {
        var group = win.add("group");
        group.alignChildren = ["left", "center"];
        var caption = group.add("statictext", undefined, label);
        caption.preferredSize.width = 170;
        var button = group.add("button", undefined, action);
        var status = group.add("statictext", undefined, empty);
        status.preferredSize.width = 170;
        caption.helpTip = button.helpTip = status.helpTip = tip;
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

    var raws = picker("Totality RAW photos", "none chosen", "Choose…",
        "The RAW photos of the totality, of one camera. AEL leaves out what it cannot stack (another camera or ISO, " +
        "the diamond ring, another pointing of the mount) and says why.");
    raws.button.onClick = function () { choose(raws, "RAW photos of the totality (select them all)"); };
    var darks = picker("Darks (optional)", "none", "Choose…",
        "Dark frames of the same camera and ISO, with the lens covered: AEL makes a master dark for each exposure of " +
        "the photos. One that is not a dark is left out, and the receipt says why.");
    darks.button.onClick = function () { choose(darks, "Dark frames of the same camera"); };
    var flats = picker("Flats (optional)", "none", "Choose…",
        "Flat frames of the same camera and optics, of an even light: AEL makes a master flat. It removes the " +
        "vignetting and the dust shadows. One that is not a flat is left out, and the receipt says why.");
    flats.button.onClick = function () { choose(flats, "Flat frames of the same camera and optics"); };

    // The filter layers: AEL's three default ones, or what the advanced settings choose
    var choice = AELPhotoshop.defaultFilters();
    var filtersRow = win.add("group");
    filtersRow.alignChildren = ["left", "center"];
    var choiceLine = filtersRow.add("statictext", undefined, "", {multiline: true});
    choiceLine.preferredSize = [330, 48];
    var advanced = filtersRow.add("button", undefined, "Advanced settings…");
    advanced.helpTip = "Choose other filters than AEL's three default layers, and their opacities";
    function showChoice() {
        choiceLine.text = AELPhotoshop.choiceText(choice);
        choiceLine.helpTip = choiceLine.text + ". AEL's three default layers unless the advanced settings choose others.";
    }
    showChoice();
    advanced.onClick = function () {
        var picked = AELPhotoshopAdvanced(choice);
        if (!picked) return;
        choice = picked;
        showChoice();
    };

    // Each run makes a new folder, named with its date and time, inside this one.
    var output = picker("Output folder", "", "Browse…",
        "Where the results go. Each run makes a new folder inside it, named with the date and time, so nothing is " +
        "overwritten. It starts at Downloads, then at the folder used last time.");
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

    // The whole library, for whoever wants more than this dialog
    var moreRow = win.add("group");
    moreRow.alignChildren = ["left", "center"];
    var more = moreRow.add("statictext", undefined, AELPhotoshop.invitation, {multiline: true});
    more.preferredSize = [380, 34];
    try {
        more.graphics.foregroundColor = more.graphics.newPen(more.graphics.PenType.SOLID_COLOR, [0.5, 0.5, 0.5], 1);
    } catch (noColour) {}
    var github = moreRow.add("button", undefined, "GitHub");
    github.helpTip = AELPhotoshop.githubUrl;
    github.onClick = function () { AELPhotoshop.openUrl(AELPhotoshop.githubUrl); };

    var buttons = win.add("group");
    buttons.alignment = "right";
    var cancel = buttons.add("button", undefined, "Cancel", {name: "cancel"});
    cancel.helpTip = "Close without making anything";
    var run = buttons.add("button", undefined, "Make the image", {name: "ok"});
    run.helpTip = "Stack the photos, make the filter layers and open the layered image here. A window shows each " +
        "step; its Stop button asks AEL to stop at its next step.";
    var answer = null;
    run.onClick = function () {
        if (!raws.files.length) {
            alert("Choose the RAW photos of the totality first.");
            return;
        }
        AELPhotoshop.saveOutput(output.folder.fsName);
        answer = {raw: raws.files, darks: darks.files, flats: flats.files, output: output.folder.fsName, choice: choice};
        win.close(1);
    };
    cancel.onClick = function () { win.close(0); };
    if (win.show() !== 1) return null;
    return answer;
};

// The advanced settings: which of AEL's filters become layers, and the opacity of each. A layer at 0 % is added hidden.
// Returns the new choice, or null when the window is closed with Cancel.
var AELPhotoshopAdvanced = function (choice) {
    var win = new Window("dialog", "Advanced settings");
    win.orientation = "column";
    win.alignChildren = "fill";
    win.spacing = 6;
    win.margins = 14;
    var intro = win.add("statictext", undefined,
        "Each filter you tick becomes a layer, in its blend mode and at its opacity. One at 0 % is added hidden, to " +
        "turn on by hand. Rest the pointer on a filter to see what it shows.", {multiline: true});
    intro.preferredSize = [460, 50];
    var rows = [], i;
    for (i = 0; i < AELPhotoshop.FILTERS.length; i++) {
        var filter = AELPhotoshop.FILTERS[i];
        var row = win.add("group");
        row.alignChildren = ["left", "center"];
        var check = row.add("checkbox", undefined, filter.label);
        check.preferredSize.width = 250;
        check.helpTip = filter.about;
        check.value = AELPhotoshop.has(choice.filters, filter.name);
        var mode = row.add("statictext", undefined, filter.mode);
        mode.preferredSize.width = 70;
        mode.helpTip = filter.about;
        var opacity = row.add("edittext", undefined,
            String(Math.round(100 * (check.value ? (choice.opacities[filter.name] || 0) : filter.opacity))));
        opacity.characters = 4;
        opacity.helpTip = "Opacity of the layer (0 %: added hidden)";
        row.add("statictext", undefined, "%");
        rows.push({name: filter.name, check: check, opacity: opacity});
    }
    function set(picked) {
        for (var k = 0; k < rows.length; k++) {
            rows[k].check.value = AELPhotoshop.has(picked.filters, rows[k].name);
            rows[k].opacity.text = String(Math.round(100 * (picked.opacities[rows[k].name] || 0)));
        }
    }

    var buttons = win.add("group");
    buttons.alignment = "right";
    var defaults = buttons.add("button", undefined, "AEL defaults");
    defaults.helpTip = "AEL's three default layers, at their opacities: NRGF, edge-aware WOW and ACHF 1–16 px";
    var all = buttons.add("button", undefined, "All 16");
    all.helpTip = "Every filter as a layer; only those with an opacity above 0 % are visible";
    var cancel = buttons.add("button", undefined, "Cancel", {name: "cancel"});
    cancel.helpTip = "Keep the filters as they were";
    var ok = buttons.add("button", undefined, "OK", {name: "ok"});
    ok.helpTip = "Use these filters";
    var answer = null;
    defaults.onClick = function () { set(AELPhotoshop.defaultFilters()); };
    all.onClick = function () {
        for (var k = 0; k < rows.length; k++) rows[k].check.value = true;
    };
    ok.onClick = function () {
        var picked = {filters: [], opacities: {}}, k;
        for (k = 0; k < rows.length; k++) {
            if (!rows[k].check.value) continue;
            var text = String(rows[k].opacity.text);
            if (!/^\s*\d{1,3}\s*$/.test(text) || Number(text) > 100) {
                alert("The opacity of " + rows[k].check.text + " must be a whole number from 0 to 100.");
                return;
            }
            picked.filters.push(rows[k].name);
            picked.opacities[rows[k].name] = Number(text) / 100;
        }
        if (!picked.filters.length) {
            alert("Tick at least one filter.");
            return;
        }
        picked.filters = AELPhotoshop.orderedFilters(picked.filters);
        answer = picked;
        win.close(1);
    };
    cancel.onClick = function () { win.close(0); };
    if (win.show() !== 1) return null;
    return answer;
};
