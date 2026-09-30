#target photoshop
// Regenera la cantonada del logo (V86 i posteriors) — Claude, 23-09-2026.
// Què fa: Photoshop compon les capes visibles de SOTA de la capa «Cantonada del logo · es regenera», en desa la caixa del racó
// inferior dret de l'enquadrament final en un TIFF temporal, a5_cantonada.py hi continua el cel (mateixa recepta que la V79,
// declarada al whitepaper) i el resultat substitueix els píxels d'aquesta capa. Tot queda en UN sol pas de l'historial (Cmd+Z el desfà).
// Ús: amb el document obert, Fitxer > Scripts > Explora… i tria aquest fitxer. No desa el document: ho decideixes tu.
var CANTONADA_V86 = (function () {
    var NOM = 'Cantonada del logo · es regenera';
    var CAIXA = [7356, 4320, 9348, 6263];            // x0, y0, x1, y1 al llenç 10551×7506 (a5_cantonada.caixa_cantonada)
    var EINES = new File($.fileName).parent;
    var HOME = Folder('~').fsName;
    var CANDIDATS = [HOME + '/.venvs/eines-ia-py312/bin/python', '/opt/homebrew/bin/python3.12', '/opt/homebrew/bin/python3', '/usr/bin/python3'];
    function python() {       // cap intèrpret escrit a pèl: el primer que tingui numpy, scipy i tifffile
        for (var i = 0; i < CANDIDATS.length; i++) {
            if (!new File(CANDIDATS[i]).exists) continue;
            if (app.system('"' + CANDIDATS[i] + '" -c "import numpy, scipy, tifffile"') === 0) return CANDIDATS[i];
        }
        throw Error('Cap Python amb numpy, scipy i tifffile. Repara l\'entorn: ~/.venvs/eines-ia-py312/bin/pip install numpy scipy tifffile');
    }
    function main() {
        var doc = app.activeDocument, capa = null, idx = -1, vis = [], i;
        if (doc.width.as('px') !== 10551 || doc.height.as('px') !== 7506) throw Error('El llenç no és el de la V86 (10551×7506).');
        for (i = 0; i < doc.layers.length; i++) { if (doc.layers[i].name === NOM) { capa = doc.layers[i]; idx = i; break; } }
        if (!capa) throw Error('No trobo la capa «' + NOM + '».');
        var py = python(), tmp = Folder.temp.fsName, entrada = new File(tmp + '/cantonada_entrada.tif'), sortida = new File(tmp + '/cantonada_sortida.tif'), rebut = new File(tmp + '/cantonada_rebut.json');
        for (i = 0; i < doc.layers.length; i++) { vis.push(doc.layers[i].visible); if (i <= idx) doc.layers[i].visible = false; }
        var dup = null;
        try {
            dup = doc.duplicate('cantonada_tmp', true);
            dup.crop([UnitValue(CAIXA[0], 'px'), UnitValue(CAIXA[1], 'px'), UnitValue(CAIXA[2], 'px'), UnitValue(CAIXA[3], 'px')]);
            if (dup.layers.length > 1 || !dup.activeLayer.isBackgroundLayer) dup.flatten();
            var t = new TiffSaveOptions(); t.imageCompression = TIFFEncoding.NONE; t.embedColorProfile = true; t.layers = false; t.alphaChannels = false; t.byteOrder = ByteOrder.IBM;
            dup.saveAs(entrada, t, true, Extension.LOWERCASE);
        } finally {
            if (dup) dup.close(SaveOptions.DONOTSAVECHANGES);
            app.activeDocument = doc;
            for (i = 0; i < doc.layers.length; i++) doc.layers[i].visible = vis[i];
        }
        var rc = app.system('"' + py + '" "' + EINES.fsName + '/a5_cantonada.py" --entrada "' + entrada.fsName + '" --sortida "' + sortida.fsName + '" --x0 ' + CAIXA[0] + ' --y0 ' + CAIXA[1] + ' --rebut "' + rebut.fsName + '"');
        if (rc !== 0 || !sortida.exists) throw Error('a5_cantonada.py ha fallat (codi ' + rc + ').');
        var res = app.open(sortida), nova = null;
        try {
            res.colorProfileName = doc.colorProfileName;
            if (res.activeLayer.isBackgroundLayer) throw Error('El TIFF de sortida no porta transparència.');
            nova = res.activeLayer.duplicate(doc, ElementPlacement.PLACEATBEGINNING);
        } finally { res.close(SaveOptions.DONOTSAVECHANGES); }
        app.activeDocument = doc;
        nova.move(capa, ElementPlacement.PLACEBEFORE);
        var b = nova.bounds; nova.translate(UnitValue(CAIXA[0] - b[0].as('px'), 'px'), UnitValue(CAIXA[1] - b[1].as('px'), 'px'));
        b = nova.bounds; if (b[0].as('px') !== CAIXA[0] || b[1].as('px') !== CAIXA[1] || b[2].as('px') !== CAIXA[2] || b[3].as('px') !== CAIXA[3]) throw Error('Posició inesperada: ' + b);
        nova.name = NOM; nova.blendMode = BlendMode.NORMAL; nova.opacity = 100; nova.visible = capa.visible;
        capa.remove(); doc.activeLayer = nova;
    }
    return main;
})();
(function () {
    var dialogs = app.displayDialogs, units = app.preferences.rulerUnits;
    try { app.displayDialogs = DialogModes.NO; app.preferences.rulerUnits = Units.PIXELS; app.activeDocument.suspendHistory('Regenera la cantonada del logo', 'CANTONADA_V86()'); }
    finally { app.displayDialogs = dialogs; app.preferences.rulerUnits = units; }
})();
'CANTONADA_REGENERADA';
