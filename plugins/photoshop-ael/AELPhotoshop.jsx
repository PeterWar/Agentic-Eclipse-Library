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
            var result = AELPhotoshop.run(options);
            var message = "AEL " + (result.ael_version || "") + " completed. " + result.opened_documents.length +
                " result document(s) opened.";
            // A PSB that Photoshop reads differently from what AEL wrote stops the run (requireNativeCheck).
            if (result.native_check) message += "\nLayered PSB checked in Photoshop: OK, " + result.native_check.layers + " layers.";
            alert(message + "\nReceipt: " + result.bridge_receipt);
        }
    } catch (error) {
        alert("AEL could not complete:\n" + error.message);
    }
}());
