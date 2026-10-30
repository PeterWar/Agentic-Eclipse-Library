/*
MIT License
Copyright (c) 2026 Pere Guerra Serra
Processed with Agentic Eclipse Library by Pere Guerra —
https://github.com/PeterWar/Agentic-Eclipse-Library
*/

var AELPhotoshop = AELPhotoshop || {};

(function (ns) {
    ns.pluginFolder = new File($.fileName).parent;
    ns.runner = new File(ns.pluginFolder.fsName + "/python/ael_photoshop.py");

    ns.jsonString = function (value) {
        var i, parts, key;
        if (value === null || value === undefined) return "null";
        if (typeof value === "number") return isFinite(value) ? String(value) : "null";
        if (typeof value === "boolean") return value ? "true" : "false";
        if (typeof value === "string") {
            return '"' + value.replace(/\\/g, "\\\\").replace(/"/g, '\\"')
                .replace(/\r/g, "\\r").replace(/\n/g, "\\n").replace(/\t/g, "\\t") + '"';
        }
        if (value instanceof Array) {
            parts = [];
            for (i = 0; i < value.length; i++) parts.push(ns.jsonString(value[i]));
            return "[" + parts.join(",") + "]";
        }
        if (value instanceof File || value instanceof Folder) return ns.jsonString(value.fsName);
        if (typeof value === "object") {
            parts = [];
            for (key in value) {
                if (value.hasOwnProperty(key) && typeof value[key] !== "function") {
                    parts.push(ns.jsonString(String(key)) + ":" + ns.jsonString(value[key]));
                }
            }
            return "{" + parts.join(",") + "}";
        }
        return "null";
    };

    ns.readJSON = function (file) {
        file.encoding = "UTF8";
        if (!file.open("r")) throw new Error("Cannot read " + file.fsName);
        var text = file.read();
        file.close();
        // ExtendScript has no reliable JSON.parse; only plain JSON (json2.js test, plus the
        // NaN/Infinity that Python writes) may reach eval.
        if (!/^[\],:{}\s]*$/.test(text.replace(/\\(?:["\\\/bfnrt]|u[0-9a-fA-F]{4})/g, "@")
                .replace(/"[^"\\\n\r]*"|true|false|null|NaN|-?Infinity|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?/g, "]")
                .replace(/(?:^|:|,)(?:\s*\[)+/g, ""))) {
            throw new Error("Refusing a result that is not plain JSON: " + file.fsName);
        }
        return eval("(" + text + ")");
    };

    ns.writeJSON = function (file, value) {
        file.encoding = "UTF8";
        file.lineFeed = "Unix";
        if (!file.open("w")) throw new Error("Cannot write " + file.fsName);
        file.write(ns.jsonString(value));
        file.close();
    };

    ns.shellQuote = function (value) {
        return "'" + String(value).replace(/'/g, "'\\''") + "'";
    };

    ns.uniqueFolder = function (parent, prefix) {
        var now = new Date();
        function two(n) { return n < 10 ? "0" + n : String(n); }
        var stamp = now.getFullYear() + two(now.getMonth() + 1) + two(now.getDate()) + "_" +
            two(now.getHours()) + two(now.getMinutes()) + two(now.getSeconds()) + "_" + now.getMilliseconds();
        var folder = new Folder(parent.fsName + "/" + prefix + stamp);
        var suffix = 0;
        while (folder.exists) {
            suffix++;
            folder = new Folder(parent.fsName + "/" + prefix + stamp + "_" + suffix);
        }
        if (!folder.create()) throw new Error("Cannot create output folder " + folder.fsName);
        return folder;
    };

    ns.pythonCandidates = function (selected) {
        var home = Folder("~").fsName;
        var candidates = selected ? [selected] : [home + "/.venvs/eines-ia-py312/bin/python",
            home + "/.venvs/eines-ia-py312/bin/python3", "/opt/homebrew/bin/python3.12",
            "/opt/homebrew/bin/python3", "/usr/local/bin/python3"];
        var answer = [], seen = {}, i, path;
        for (i = 0; i < candidates.length; i++) {
            path = candidates[i] ? new File(candidates[i]).fsName : "";
            if (path && !seen[path] && new File(path).exists) {
                seen[path] = true;
                answer.push(path);
            }
        }
        return answer;
    };

    ns.runPython = function (python, cfg, runRoot, aelFolder) {
        var config = new File(runRoot.fsName + "/config.json");
        var result = new File(runRoot.fsName + "/result.json");
        ns.writeJSON(config, cfg);
        var env = aelFolder ? new Folder(aelFolder).fsName : "";
        var command = "/usr/bin/env " + ns.shellQuote("PYTHONDONTWRITEBYTECODE=1") + " " +
            ns.shellQuote("PYTHONPATH=" + env) + " " + ns.shellQuote(python) + " " +
            ns.shellQuote(ns.runner.fsName) + " " + ns.shellQuote(config.fsName) + " " +
            ns.shellQuote(result.fsName);
        var code = app.system(command);
        if (!result.exists) throw new Error("Python returned no result (exit " + code + ")");
        var answer = ns.readJSON(result);
        if (!answer.ok) throw new Error(answer.message || ("AEL failed with exit " + code));
        answer.python_exit = code;
        return answer;
    };

    ns.probe = function (selected, aelFolder) {
        var candidates = ns.pythonCandidates(selected);
        if (!candidates.length) throw new Error("bad_path: select an existing Python 3.10+ executable");
        var errors = [];
        for (var i = 0; i < candidates.length; i++) {
            var root = ns.uniqueFolder(Folder.temp, "AEL_PS_probe_");
            try {
                var answer = ns.runPython(candidates[i], {operation: "probe"}, root, aelFolder);
                answer.selected_python = candidates[i];
                return answer;
            } catch (error) {
                errors.push(candidates[i] + ": " + error.message);
            } finally {
                var files = root.getFiles();
                for (var j = 0; j < files.length; j++) if (files[j] instanceof File) files[j].remove();
                root.remove();
            }
        }
        throw new Error("No suitable Python/AEL runtime. " + errors.join(" | "));
    };

    ns.exportDocument = function (doc, target) {
        if (target.exists) throw new Error("Refusing to overwrite " + target.fsName);
        if (doc.mode !== DocumentMode.RGB && doc.mode !== DocumentMode.GRAYSCALE) {
            throw new Error("Convert a copy to RGB or grayscale before running AEL");
        }
        var temporary = null;
        var beforeSaved = doc.saved;
        try {
            temporary = doc.duplicate("AEL temporary export", true);
            var options = new TiffSaveOptions();
            options.imageCompression = TIFFEncoding.NONE;
            options.layers = false;
            options.alphaChannels = false;
            // Without transparency Photoshop fills transparent pixels with white. With it,
            // Photoshop adds an alpha sample only when such pixels exist, and the runner refuses them.
            options.transparency = true;
            options.embedColorProfile = true;
            options.byteOrder = ByteOrder.IBM;
            temporary.saveAs(target, options, true, Extension.LOWERCASE);
        } finally {
            if (temporary) temporary.close(SaveOptions.DONOTSAVECHANGES);
            app.activeDocument = doc;
        }
        if (doc.saved !== beforeSaved) throw new Error("Source document saved-state changed unexpectedly");
        var profile = null;
        if (doc.colorProfileType !== ColorProfile.NONE) profile = doc.colorProfileName;
        return {name: doc.name, id: doc.id, width: doc.width.as("px"), height: doc.height.as("px"),
            channels: doc.mode === DocumentMode.RGB ? 3 : 1,
            bits_per_channel: doc.bitsPerChannel.toString(), color_profile: profile,
            color_profile_type: doc.colorProfileType.toString(),
            saved_before: beforeSaved, saved_after: doc.saved};
    };

    ns.documentIDs = function () {
        var ids = {};
        for (var i = 0; i < app.documents.length; i++) ids[String(app.documents[i].id)] = true;
        return ids;
    };

    ns.openResults = function (result) {
        var opened = [], known = ns.documentIDs();
        for (var i = 0; i < result.images.length; i++) {
            var file = new File(result.images[i].path);
            var doc;
            try {
                doc = app.open(file);
            } catch (error) {
                throw new Error("Opened " + opened.length + " of " + result.images.length +
                    " result documents, then failed on " + file.fsName + ": " + error.message +
                    ". The opened results stay open; no other document was touched.");
            }
            if (known[String(doc.id)]) throw new Error("Refusing to reuse an already open document: " + file.fsName);
            known[String(doc.id)] = true;
            doc.name = "AEL " + result.images[i].name;
            opened.push({id: doc.id, name: doc.name, path: file.fsName});
        }
        result.opened_documents = opened;
        return opened;
    };

    ns.run = function (options) {
        if (!ns.runner.exists) throw new Error("Missing Python runner: " + ns.runner.fsName);
        var probe = ns.probe(options.python, options.aelFolder);
        options.python = probe.selected_python;
        var parent = new Folder(options.outputParent);
        if (!parent.exists) throw new Error("Output parent does not exist: " + parent.fsName);
        var root = ns.uniqueFolder(parent, "AEL_");
        var oldDialogs = app.displayDialogs;
        var oldUnits = app.preferences.rulerUnits;
        var source = null;
        try {
            app.displayDialogs = DialogModes.NO;
            app.preferences.rulerUnits = Units.PIXELS;
            options.run_root = root.fsName;
            options.out = root.fsName + "/" + options.operation;
            if (options.operation === "structure" || options.operation === "polar") {
                if (!app.documents.length) throw new Error("Open an RGB or grayscale source document first");
                var geometry = new File(options.geometry);
                if (!geometry.exists) throw new Error("Select an EclipseGeometry JSON file");
                var doc = app.activeDocument;
                var input = new File(root.fsName + "/source.tif");
                source = ns.exportDocument(doc, input);
                options.input = input.fsName;
                options.source = {width: source.width, height: source.height, channels: source.channels};
                options.source_document = source;
                var geometryCopy = new File(root.fsName + "/input_geometry.json");
                geometry.copy(geometryCopy);
                options.geometry = geometryCopy.fsName;
            }
            var result = ns.runPython(options.python, options, root, options.aelFolder);
            ns.openResults(result);
            result.run_root = root.fsName;
            result.source_document = source;
            return result;
        } finally {
            app.displayDialogs = oldDialogs;
            app.preferences.rulerUnits = oldUnits;
        }
    };
}(AELPhotoshop));
