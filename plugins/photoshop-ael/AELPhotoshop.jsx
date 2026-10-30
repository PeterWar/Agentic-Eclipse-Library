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
            alert("AEL completed. " + result.opened_documents.length +
                " result document(s) opened.\nReceipt: " + result.bridge_receipt);
        }
    } catch (error) {
        alert("AEL could not complete:\n" + error.message);
    }
}());
