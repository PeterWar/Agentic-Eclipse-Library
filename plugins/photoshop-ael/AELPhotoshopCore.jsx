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

    // The Python that worked last time, kept in Photoshop's custom options: the first candidate of the next run.
    ns.settingsKey = "AELPhotoshop-python-e3b1c7a2";
    ns.savedPython = function () {
        try {
            return app.getCustomOptions(ns.settingsKey).getString(stringIDToTypeID("python"));
        } catch (missing) {
            return "";
        }
    };
    ns.savePython = function (path) {
        try {
            var settings = new ActionDescriptor();
            settings.putString(stringIDToTypeID("python"), path);
            app.putCustomOptions(ns.settingsKey, settings, true);
        } catch (ignored) {}
    };

    // python3, then python3.N from the newest minor version to the oldest, in one folder.
    ns.versionedPythons = function (directory) {
        var files = new Folder(directory).getFiles("python3*") || [], found = [], i;
        function minor(path) {
            var match = /python3\.([0-9]+)$/.exec(path);
            return match ? parseInt(match[1], 10) : 1000;
        }
        for (i = 0; i < files.length; i++) {
            if (files[i] instanceof File && /\/python3(\.[0-9]+)?$/.test(files[i].fsName)) found.push(files[i].fsName);
        }
        found.sort(function (a, b) { return minor(b) - minor(a); });
        return found;
    };

    // The script names no interpreter. A Python chosen in the dialog is the only candidate; otherwise, in this order:
    // the one that worked last time, AEL_PYTHON, python3 and python3.N (newest first) in /opt/homebrew/bin and
    // /usr/local/bin, virtual environments (~/.venvs/*, ~/.virtualenvs/*, ~/venvs/*, ~/venv, ~/.venv), pyenv, conda
    // and /usr/bin/python3. Each existing one is tried in turn; the first that runs AEL with its dependencies wins.
    ns.pythonCandidates = function (selected) {
        var home = Folder("~").fsName, candidates = [], i, j;
        if (selected) {
            candidates.push(selected);
        } else {
            candidates.push(ns.savedPython(), $.getenv("AEL_PYTHON"));
            candidates = candidates.concat(ns.versionedPythons("/opt/homebrew/bin"), ns.versionedPythons("/usr/local/bin"));
            var environments = [home + "/.venvs", home + "/.virtualenvs", home + "/venvs"];
            for (i = 0; i < environments.length; i++) {
                var entries = new Folder(environments[i]).getFiles() || [], folders = [];
                for (j = 0; j < entries.length; j++) if (entries[j] instanceof Folder) folders.push(entries[j].fsName);
                folders.sort();
                for (j = 0; j < folders.length; j++) candidates.push(folders[j] + "/bin/python");
            }
            candidates.push(home + "/venv/bin/python", home + "/.venv/bin/python", home + "/.pyenv/shims/python",
                home + "/miniconda3/bin/python", home + "/anaconda3/bin/python", home + "/miniforge3/bin/python",
                home + "/mambaforge/bin/python", "/usr/bin/python3");
        }
        var answer = [], seen = {}, path;
        for (i = 0; i < candidates.length; i++) {
            path = candidates[i] ? new File(candidates[i]).fsName : "";
            if (path && !seen[path] && new File(path).exists) {
                seen[path] = true;
                answer.push(path);
            }
        }
        return answer;
    };

    // AEL used when the dialog names no folder: the engine bundled with this script, then the checkout
    // that contains it (plugins/photoshop-ael inside the repository), then whatever Python has installed.
    ns.defaultAELFolder = function () {
        var bundled = new File(ns.pluginFolder.fsName + "/runtime/ael/__init__.py");
        if (bundled.exists) return bundled.parent.parent.fsName;
        var checkout = new File(ns.pluginFolder.parent.parent.fsName + "/ael/__init__.py");
        if (checkout.exists) return checkout.parent.parent.fsName;
        return "";
    };

    ns.runPython = function (python, cfg, runRoot, aelFolder) {
        var config = new File(runRoot.fsName + "/config.json");
        var result = new File(runRoot.fsName + "/result.json");
        ns.writeJSON(config, cfg);
        var env = aelFolder ? new Folder(aelFolder).fsName : ns.defaultAELFolder();
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
        if (selected && !candidates.length) throw new Error("bad_path: select an existing Python 3.10+ executable");
        var answer = ns.firstWorking(candidates, aelFolder);
        ns.savePython(answer.selected_python);
        return answer;
    };

    // The first candidate that answers the runner's probe; the ones that failed before it are kept in ``tried``.
    ns.firstWorking = function (candidates, aelFolder) {
        var errors = [];
        for (var i = 0; i < candidates.length; i++) {
            var root = ns.uniqueFolder(Folder.temp, "AEL_PS_probe_");
            try {
                var answer = ns.runPython(candidates[i], {operation: "probe"}, root, aelFolder);
                answer.selected_python = candidates[i];
                answer.tried = errors;
                return answer;
            } catch (error) {
                errors.push(candidates[i] + ": " + error.message);
            } finally {
                var files = root.getFiles();
                for (var j = 0; j < files.length; j++) if (files[j] instanceof File) files[j].remove();
                root.remove();
            }
        }
        throw new Error("No Python 3.10+ with AEL and its dependencies was found. Select the Python executable in the " +
            "dialog, or install the dependencies: python -m pip install numpy scipy opencv-python-headless pillow " +
            "tifffile imageio psd-tools. Tried: " + (errors.length ? errors.join(" | ") : "no Python in the usual folders"));
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

    // The layered PSB as Photoshop itself reads it, against the layers AEL wrote (bottom up): name, blend
    // mode, opacity (AEL stores it in 8 bits) and visibility. AEL's own check reads the file back with
    // psd-tools only.
    ns.checkLayers = function (doc, expected) {
        var found = [], problems = [], i, k;
        for (i = doc.layers.length - 1; i >= 0; i--) {
            var layer = doc.layers[i];
            found.push({name: layer.name, mode: String(layer.blendMode), opacity: layer.opacity,
                visible: layer.visible, type: layer.typename});
        }
        if (found.length !== expected.length) problems.push(found.length + " layers, expected " + expected.length);
        for (k = 0; k < Math.min(found.length, expected.length); k++) {
            var want = expected[k], got = found[k];
            if (got.name !== want.name) problems.push("layer " + (k + 1) + " is " + got.name + ", expected " + want.name);
            if (got.mode !== "BlendMode." + String(want.mode).toUpperCase()) problems.push(want.name + ": " + got.mode);
            // Photoshop reports byte b as b / 255 × 100 %: compare the byte itself, as AEL rounded it in Python.
            var stored = want.opacity_byte !== undefined ? want.opacity_byte : Math.round(want.opacity * 255);
            if (Math.round(got.opacity * 255 / 100) !== stored) {
                problems.push(want.name + ": opacity " + got.opacity + " %, expected " + stored + "/255");
            }
            if (Boolean(got.visible) !== Boolean(want.visible)) problems.push(want.name + ": visible " + got.visible);
        }
        return {ok: problems.length === 0, layers: found.length, expected: expected.length,
            bits: String(doc.bitsPerChannel), problems: problems, found: found};
    };

    // app.open() of a file that is already open returns that document, with whatever is unsaved in it.
    ns.isOpen = function (file) {
        var target = new File(file).fsName;
        for (var i = 0; i < app.documents.length; i++) {
            try {
                if (app.documents[i].fullName.fsName === target) return true;
            } catch (unsaved) {}
        }
        return false;
    };

    ns.openResults = function (result) {
        var opened = [], known = ns.documentIDs();
        var list = result.open || result.images;
        for (var i = 0; i < list.length; i++) {
            var file = new File(list[i].path);
            var doc;
            if (ns.isOpen(file)) throw new Error("Already open in Photoshop, not touched: " + file.fsName +
                ". Opened " + opened.length + " of " + list.length + " result documents.");
            try {
                doc = app.open(file);
            } catch (error) {
                throw new Error("Opened " + opened.length + " of " + list.length +
                    " result documents, then failed on " + file.fsName + ": " + error.message +
                    ". The opened results stay open; no other document was touched.");
            }
            if (known[String(doc.id)]) throw new Error("Refusing to reuse an already open document: " + file.fsName);
            known[String(doc.id)] = true;
            opened.push({id: doc.id, name: doc.name, path: file.fsName, kind: list[i].kind || ""});
            if (list[i].kind === "psb" && result.psb_expected) result.native_check = ns.checkLayers(doc, result.psb_expected);
        }
        result.opened_documents = opened;
        return opened;
    };

    // The check inside Photoshop decides the run: a PSB that Photoshop reads differently from what AEL wrote is an
    // error, with its documents left open to look at and the differences in AEL_PHOTOSHOP_NATIVE_CHECK.json.
    ns.requireNativeCheck = function (result) {
        var check = result.native_check;
        if (check && !check.ok) {
            throw new Error("The layered PSB that Photoshop opened is not what AEL wrote: " + check.problems.join("; ") +
                ". Its documents stay open." + (result.native_check_file ? " Details: " + result.native_check_file : ""));
        }
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
            result.ael_version = probe.runtime ? probe.runtime.ael_version : null;
            if (result.native_check) {
                result.native_check_file = root.fsName + "/AEL_PHOTOSHOP_NATIVE_CHECK.json";
                ns.writeJSON(new File(result.native_check_file), result.native_check);
            }
            ns.requireNativeCheck(result);
            return result;
        } finally {
            app.displayDialogs = oldDialogs;
            app.preferences.rulerUnits = oldUnits;
        }
    };

    // --- RAW photos in, a layered PSB out ------------------------------------------------------------------
    // Where the results go: a new folder for each run, named with its date and time, inside the output folder of the
    // dialog. The dialog starts at the folder used last time while it exists, otherwise at Downloads, as the
    // PixInsight connector does. The folder is kept in Photoshop's custom options, like the Python.
    ns.outputKey = "AELPhotoshop-output-e3b1c7a2";
    ns.savedOutput = function () {
        try {
            return app.getCustomOptions(ns.outputKey).getString(stringIDToTypeID("folder"));
        } catch (missing) {
            return "";
        }
    };
    ns.saveOutput = function (path) {
        try {
            var settings = new ActionDescriptor();
            settings.putString(stringIDToTypeID("folder"), path);
            app.putCustomOptions(ns.outputKey, settings, true);
        } catch (ignored) {}
    };
    ns.defaultOutput = function () {
        var saved = ns.savedOutput();
        if (saved && new Folder(saved).exists) return new Folder(saved);
        return new Folder(Folder("~").fsName + "/Downloads");
    };

    // AEL's filters, as the library names them (ael.filterbank.NAMES, ael.develop.layer_names), listed as the PixInsight
    // connector lists them (tools/check_connectors.py keeps the two lists the same): the layer's name, its blend mode,
    // its opacity (AEL's three default layers; at 0 the layer is added hidden, to turn on by hand) and what it shows.
    ns.FILTERS = [
        {name: "nrgf", label: "01 NRGF", mode: "Multiply", opacity: 0.39,
            about: "Normalising radial graded filter: each radius scaled by its own spread, so the corona's " +
                "shape shows from the limb outwards."},
        {name: "nrgf_log", label: "01 NRGF log", mode: "Multiply", opacity: 0,
            about: "The NRGF on the logarithm of the brightness: softer in the bright inner corona."},
        {name: "rhef", label: "02 RHEF", mode: "Multiply", opacity: 0,
            about: "Radial histogram equalisation: each radius spread over the whole tonal range."},
        {name: "rhef_upsilon", label: "02 RHEF Upsilon", mode: "Multiply", opacity: 0,
            about: "Radial histogram equalisation with the Upsilon curve, gentler at both ends."},
        {name: "rhef_local60", label: "02 RHEF local 60°", mode: "Multiply", opacity: 0,
            about: "Radial histogram equalisation in sectors of 60 degrees: each sector against its own range."},
        {name: "rhef_local30", label: "02 RHEF local 30°", mode: "Multiply", opacity: 0,
            about: "Radial histogram equalisation in sectors of 30 degrees."},
        {name: "mgn", label: "03 MGN", mode: "Overlay", opacity: 0,
            about: "Multi-scale Gaussian normalisation (Morgan and Druckmüller): fine structure at every scale."},
        {name: "achf_angular", label: "04 ACHF angular", mode: "Overlay", opacity: 0,
            about: "Angular high-pass: detail across the rays, along the position angle."},
        {name: "achf_angular4", label: "04 ACHF angular smoothed 4 px", mode: "Overlay", opacity: 0,
            about: "Angular high-pass, smoothed over 4 pixels along the radius."},
        {name: "achf_angular8", label: "04 ACHF angular smoothed 8 px", mode: "Overlay", opacity: 0,
            about: "Angular high-pass, smoothed over 8 pixels along the radius."},
        {name: "achf_iso_01", label: "04 ACHF iso 2–32 px", mode: "Overlay", opacity: 0,
            about: "Isotropic high-pass of the detail between 2 and 32 pixels."},
        {name: "achf_iso_04", label: "04 ACHF iso 1–16 px", mode: "Overlay", opacity: 0.08,
            about: "Isotropic high-pass of the finest detail, 1 to 16 pixels."},
        {name: "achf_iso_05", label: "04 ACHF iso 2–48 px", mode: "Overlay", opacity: 0,
            about: "Isotropic high-pass of the detail between 2 and 48 pixels."},
        {name: "achf_iso_06", label: "04 ACHF iso 4–64 px", mode: "Overlay", opacity: 0,
            about: "Isotropic high-pass of the broader detail, 4 to 64 pixels."},
        {name: "wow", label: "05 WOW", mode: "Overlay", opacity: 0,
            about: "Wavelet-based detail at every scale, each scale against its own noise."},
        {name: "wow_edge_aware", label: "05 WOW edge-aware", mode: "Overlay", opacity: 0.37,
            about: "Wavelet-based detail that keeps the edges of the structure sharp."}
    ];
    // AEL's default layers in the order the engine stacks them (ael.filterbank.DEFAULTS): Overlay does not commute.
    ns.DEFAULT_ORDER = ["nrgf", "wow_edge_aware", "achf_iso_04"];

    ns.has = function (list, value) {
        for (var i = 0; i < list.length; i++) if (list[i] === value) return true;
        return false;
    };
    // The filters chosen, in the order they are stacked: AEL's default ones first, in their order, then the others as
    // listed.
    ns.orderedFilters = function (names) {
        var ordered = [], i;
        for (i = 0; i < ns.DEFAULT_ORDER.length; i++) {
            if (ns.has(names, ns.DEFAULT_ORDER[i])) ordered.push(ns.DEFAULT_ORDER[i]);
        }
        for (i = 0; i < ns.FILTERS.length; i++) {
            if (ns.has(names, ns.FILTERS[i].name) && !ns.has(ordered, ns.FILTERS[i].name)) ordered.push(ns.FILTERS[i].name);
        }
        return ordered;
    };
    // What a run makes unless the advanced settings choose otherwise: AEL's three default layers at their opacities.
    ns.defaultFilters = function () {
        var choice = {filters: ns.DEFAULT_ORDER.slice(0), opacities: {}};
        for (var i = 0; i < ns.FILTERS.length; i++) {
            if (ns.has(ns.DEFAULT_ORDER, ns.FILTERS[i].name)) choice.opacities[ns.FILTERS[i].name] = ns.FILTERS[i].opacity;
        }
        return choice;
    };
    // The filters chosen, in one line: each visible layer with its opacity, and how many are added hidden.
    ns.choiceText = function (choice) {
        var parts = [], hidden = 0;
        for (var i = 0; i < ns.FILTERS.length; i++) {
            var filter = ns.FILTERS[i];
            if (!ns.has(choice.filters, filter.name)) continue;
            var opacity = Math.round(100 * (choice.opacities[filter.name] || 0));
            // the number and its % stay together
            if (opacity > 0) parts.push(filter.label.replace(/^\d+[a-z]? /, "") + " " + opacity + "\u00a0%");
            else hidden++;
        }
        return "Filter layers: " + (parts.length ? parts.join(", ") : "none visible") +
            (hidden ? ", and " + hidden + " more, hidden" : "");
    };

    // The whole library, for whoever wants more than this dialog, and the licence (LICENSE): the same words as in the
    // PixInsight connector. The licence is one line under the address, with the whole disclaimer on its tip.
    ns.githubUrl = "https://github.com/PeterWar/Agentic-Eclipse-Library";
    ns.invitation = "For more faithful results and more filters, try the whole Agentic Eclipse Library with an AI agent:";
    ns.licenceLine = "MIT License · Copyright © 2026 Pere Guerra Serra · Provided “as is”, " +
        "without warranty of any kind.";
    ns.licenceDisclaimer = "THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, " +
        "INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR " +
        "PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE " +
        "FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR " +
        "OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER " +
        "DEALINGS IN THE SOFTWARE.";
    // A web address written as a link that opens the page when clicked: blue text (#0066ff, as in the PixInsight
    // connector) with a blue line under it. ScriptUI does not underline text, and on Photoshop 2026 for macOS a
    // control's onDraw does not draw text at all (31-10): the line is a group one pixel high, filled with blue.
    ns.addLink = function (parent, url, tip) {
        var box = parent.add("group");
        box.orientation = "column";
        box.alignChildren = "left";
        box.spacing = 0;
        var text = box.add("statictext", undefined, url);
        text.helpTip = tip;
        var line = box.add("group");
        try {
            var blue = [0, 0.4, 1, 1];
            text.graphics.foregroundColor = text.graphics.newPen(text.graphics.PenType.SOLID_COLOR, blue, 1);
            line.preferredSize = [Math.ceil(text.graphics.measureString(url, text.graphics.font)[0]), 1];
            line.graphics.backgroundColor = line.graphics.newBrush(line.graphics.BrushType.SOLID_COLOR, blue);
        } catch (plainText) {}
        text.addEventListener("mousedown", function () { ns.openUrl(url); });
        return text;
    };
    ns.openUrl = function (url) {
        if (/^win/i.test($.os)) app.system('cmd /c start "" "' + url + '"');
        else app.system("open " + ns.shellQuote(url));
    };

    ns.removeFolder = function (folder) {
        var files = folder.getFiles() || [];
        for (var i = 0; i < files.length; i++) {
            if (files[i] instanceof Folder) ns.removeFolder(files[i]); else files[i].remove();
        }
        folder.remove();
    };

    // Python runs in the background; Photoshop shows its progress and waits for its result file. Cancel writes a file
    // that stops Python at its next step; when that step is long (a filter, writing the PSB), Python is stopped after
    // STOP_GRACE_S.
    ns.STOP_GRACE_S = 15;
    ns.stoppedError = function (answer) {
        var error = new Error("Stopped: AEL did not finish, and nothing was opened.");
        error.stopped = true;
        error.answer = answer;
        return error;
    };
    ns.runBackground = function (python, cfg, runRoot, onProgress) {
        var config = new File(runRoot.fsName + "/config.json");
        var result = new File(runRoot.fsName + "/result.json");
        var log = new File(runRoot.fsName + "/python.log");
        var pid = new File(runRoot.fsName + "/pid");
        cfg.progress = runRoot.fsName + "/progress.json";
        cfg.cancel = runRoot.fsName + "/cancel";
        ns.writeJSON(config, cfg);
        var command = "/usr/bin/env " + ns.shellQuote("PYTHONDONTWRITEBYTECODE=1") + " " +
            ns.shellQuote("PYTHONPATH=" + ns.defaultAELFolder()) + " " + ns.shellQuote(python) + " " +
            ns.shellQuote(ns.runner.fsName) + " " + ns.shellQuote(config.fsName) + " " + ns.shellQuote(result.fsName) +
            " > " + ns.shellQuote(log.fsName) + " 2>&1 & echo $! > " + ns.shellQuote(pid.fsName);
        app.system(command);
        var lastCheck = new Date().getTime(), processId = "", info = null, stopAsked = 0, stopSent = false;
        while (!result.exists) {
            $.sleep(400);
            var progress = new File(cfg.progress);
            if (progress.exists) {
                try { info = ns.readJSON(progress); } catch (busy) {}
            }
            // At every turn, not only when AEL reports a new step: the window's clock and its Cancel button stay alive.
            onProgress(info);
            if (onProgress.cancelled && !stopAsked) {
                stopAsked = new Date().getTime();
                ns.writeJSON(new File(cfg.cancel), {cancel: true});
            }
            if (!processId && pid.exists) {
                pid.open("r");
                processId = String(pid.read()).replace(/\s+/g, "");
                pid.close();
            }
            var known = /^[0-9]+$/.test(processId);
            if (stopAsked && !stopSent && known && new Date().getTime() - stopAsked > ns.STOP_GRACE_S * 1000) {
                app.system("kill " + processId);
                stopSent = true;
            }
            if (new Date().getTime() - lastCheck > 5000) {
                lastCheck = new Date().getTime();
                // kill -0 only asks whether the process is still there.
                if (known && app.system("kill -0 " + processId) !== 0) {
                    $.sleep(1000);
                    if (!result.exists) {
                        if (stopAsked) throw ns.stoppedError(null);
                        throw new Error("Python stopped without an answer. Its messages are in " + log.fsName);
                    }
                }
            }
        }
        $.sleep(200);
        var answer = ns.readJSON(result);
        if (!answer.ok) {
            if (stopAsked) throw ns.stoppedError(answer);
            var error = new Error(answer.message || "AEL failed");
            error.answer = answer;
            throw error;
        }
        return answer;
    };

    // AEL's steps, in the order it takes them, and the part of the bar each one fills.
    ns.PROGRESS_STEPS = {"Starting": [0, 0], "Reading the files": [0, 10], "Combining darks": [10, 14],
        "Combining flats": [14, 17], "Finding the Moon": [17, 27], "Registering on the Sun": [27, 40],
        "Measuring the light of each photo": [40, 45], "Levelling the photos": [45, 49],
        "Looking for dust on the sensor": [49, 54], "Stacking": [54, 64], "Filters": [64, 92], "Saving": [92, 99],
        "Done": [100, 100]};
    ns.HEARTBEAT_S = 20;
    ns.clock = function (ms) {
        var s = Math.max(0, Math.round(ms / 1000));
        return Math.floor(s / 60) + ":" + (s % 60 < 10 ? "0" : "") + (s % 60);
    };
    // What the progress window says at every turn of the wait. First line: the step, its count, what AEL is on, and
    // the time since Make the image, so something moves every second. Second line: after HEARTBEAT_S on the same
    // step (one filter can take minutes), that AEL is still working on it. The bar fills step by step and never goes
    // back. ns.progressLog keeps what it said, as the PixInsight connector writes it to its Console.
    ns.progressState = function () {
        var start = new Date().getTime();
        var state = {started: start, said: "", saidAt: start, heard: start, value: 0, cancelled: false, text: ""};
        ns.progressLog = [];
        state.read = function (info) {
            var now = new Date().getTime();
            info = info || {stage: "Starting"};
            var span = ns.PROGRESS_STEPS[info.stage];
            if (span) {
                var fraction = info.total ? Math.min(1, info.done / info.total) : 0;
                state.value = Math.max(state.value, span[0] + (span[1] - span[0]) * fraction);
            }
            var step = info.stage + (info.total ? " (" + info.done + " of " + info.total + ")" : "") +
                (info.message ? ": " + info.message : "");
            if (step !== state.said) {
                ns.progressLog.push("AEL: " + step + " — " + Math.round((now - state.started) / 1000) + " s");
                state.said = step;
                state.saidAt = state.heard = now;
            } else if (now - state.heard >= ns.HEARTBEAT_S * 1000) {
                ns.progressLog.push("AEL: still working on " + step + " — " +
                    Math.round((now - state.saidAt) / 1000) + " s");
                state.heard = now;
            }
            if (state.cancelled && !state.stopping) {
                ns.progressLog.push("AEL: stopping at the end of this step — " +
                    Math.round((now - state.started) / 1000) + " s");
                state.stopping = true;
            }
            var quiet = now - state.saidAt;
            state.text = step + "  ·  " + ns.clock(now - state.started) + "\n" +
                (state.cancelled ? "Stopping: AEL stops at the end of this step." :
                quiet >= ns.HEARTBEAT_S * 1000 ? "Still working (" + ns.clock(quiet) +
                    "): a filter or writing the PSB can take minutes." :
                "The Agentic Eclipse Library is making the image.");
            return state;
        };
        return state;
    };
    // The steps are shown in Photoshop's own progress window: it is drawn, its bar and its text change, and its
    // Cancel button answers while the script waits for Python. A ScriptUI palette is not drawn at all: on Photoshop
    // 2026 for macOS it stays at 0 x 0 pixels, off screen, until the script ends (measured on 31-10), and the only sign
    // of life was the spinning wheel. Photoshop's window runs a function named in a string: runProgressJob.
    ns.withProgress = function (work) {
        var state = ns.progressState();
        var update = function (info) {
            state.read(info);
            if (ns.progressJob) {
                app.changeProgressText(state.text);
                if (!app.updateProgress(Math.round(10 * state.value), 1000)) state.cancelled = true;
            }
            update.cancelled = state.cancelled;
        };
        update.cancelled = false;
        if (typeof app.doForcedProgress === "undefined") return work(update);
        var outcome;
        ns.progressJob = {work: work, update: update, outcome: null};
        try {
            app.doForcedProgress("Agentic Eclipse Library", "AELPhotoshop.runProgressJob()");
            outcome = ns.progressJob.outcome;
        } finally {
            ns.progressJob = null;
        }
        if (!outcome) throw new Error("Photoshop's progress window did not run AEL.");
        if (outcome.failed) throw outcome.error;
        return outcome.value;
    };
    ns.runProgressJob = function () {
        var job = ns.progressJob;
        try {
            job.outcome = {value: job.work(job.update)};
        } catch (error) {
            job.outcome = {failed: true, error: error};
        }
    };

    ns.runRaw = function (options) {
        if (!ns.runner.exists) throw new Error("Missing Python runner: " + ns.runner.fsName);
        var probe = ns.probe("", "");
        var choice = options.choice || ns.defaultFilters();
        var parent = options.output ? new Folder(options.output) : ns.defaultOutput();
        if (!parent.exists && !parent.create()) throw new Error("Cannot create the output folder " + parent.fsName);
        var out = ns.uniqueFolder(parent, "AEL_");
        var runRoot = ns.uniqueFolder(Folder.temp, "AEL_PS_run_");
        var cfg = {operation: "raw", raw: options.raw, darks: options.darks || [], flats: options.flats || [],
            calibration: options.calibration || [], out: out.fsName, filters: choice.filters,
            opacities: choice.opacities};
        var oldDialogs = app.displayDialogs;
        var result;
        try {
            result = ns.withProgress(function (update) {
                return ns.runBackground(probe.selected_python, cfg, runRoot, update);
            });
        } catch (error) {
            var log = new File(runRoot.fsName + "/python.log");
            if (log.exists) log.copy(new File(out.fsName + "/AEL error log.txt"));
            if (error.answer) ns.writeJSON(new File(out.fsName + "/AEL error.json"), error.answer);
            var failure = new Error(error.message + "\n\nDetails: " + out.fsName);
            failure.stopped = error.stopped;
            throw failure;
        } finally {
            ns.removeFolder(runRoot);
        }
        try {
            app.displayDialogs = DialogModes.NO;
            var psb = new File(result.psb);
            if (ns.isOpen(psb)) throw new Error("Already open in Photoshop, not touched: " + psb.fsName);
            var known = ns.documentIDs();
            var doc = app.open(psb);
            if (known[String(doc.id)]) throw new Error("Refusing to reuse an already open document: " + psb.fsName);
            result.psb_expected = [];
            for (var i = 0; i < result.psb_layers.length; i++) {
                var layer = result.psb_layers[i];
                result.psb_expected.push({name: layer.name, mode: layer.mode, opacity: layer.opacity,
                    opacity_byte: Math.round(layer.opacity * 255), visible: layer.visible});
            }
            result.native_check = ns.checkLayers(doc, result.psb_expected);
            if (!result.native_check.ok) {
                result.native_check_file = out.fsName + "/details/photoshop_check.json";
                ns.writeJSON(new File(result.native_check_file), result.native_check);
            }
            ns.requireNativeCheck(result);
        } finally {
            app.displayDialogs = oldDialogs;
        }
        result.ael_version = probe.runtime ? probe.runtime.ael_version : null;
        return result;
    };

    ns.doneMessage = function (result) {
        var s = result.summary, left = result.left_out || [];
        var text = "Done: " + s.frames_stacked + " of " + s.frames_chosen + " photos stacked into one image " +
            "(" + s.camera + ", " + s.date + ").";
        if (left.length) {
            text += "\n\nLeft out (" + left.length + "):";
            for (var i = 0; i < Math.min(left.length, 5); i++) text += "\n• " + left[i].file + ": " + left[i].reason;
            if (left.length > 5) text += "\n• … and " + (left.length - 5) + " more, listed in the receipt";
        }
        if (s.cloudy) {
            text += "\n\nThe sky changed during the totality (thin clouds or haze): faint arcs may show where " +
                "an exposure saturates.";
        }
        text += "\n\nThe layered image is open. It is saved, with the linear master and a receipt, in:\n" + result.out;
        return text + "\n\n" + ns.invitation + " " + ns.githubUrl;
    };
}(AELPhotoshop));
