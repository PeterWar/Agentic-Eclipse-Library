#target photoshop
/*
MIT License
Copyright (c) 2026 Pere Guerra Serra
Processed with Agentic Eclipse Library by Pere Guerra —
https://github.com/PeterWar/Agentic-Eclipse-Library

Run from File > Scripts > Browse, or install in Photoshop's Scripts folder.
*/
#include "AELPhotoshopCore.jsx"
#include "AELPhotoshopDialog.jsx"

(function () {
    try {
        var options = AELPhotoshopDialog();
        if (options) {
            var result = AELPhotoshop.runRaw(options);
            alert(AELPhotoshop.doneMessage(result));
        }
    } catch (error) {
        alert("AEL could not make the image.\n\n" + error.message);
    }
}());
