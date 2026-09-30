// Prova: quin fitxer queda a la capa de dalt amb «Load Files into Stack»
var loadLayersFromScript = true;
var jsx = new File("/Applications/Adobe Photoshop 2026/Presets/Scripts/Load Files into Stack.jsx");
$.evalFile(jsx);
var dir = "/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/d71d9c5e-3aa3-4147-970b-e20c3f2a5e3e/scratchpad/ps_test/";
var llista = [new File(dir + "prova_01.jpg"), new File(dir + "prova_02.jpg"), new File(dir + "prova_03.jpg")];
var nAbans = app.documents.length;
loadLayers.intoStack(llista, false);
var doc = app.activeDocument;
var noms = [];
for (var i = 0; i < doc.layers.length; i++) noms.push(doc.layers[i].name);   // layers[0] = capa de DALT
var resultat = "de dalt a baix: " + noms.join(" | ");
if (app.documents.length > nAbans) doc.close(SaveOptions.DONOTSAVECHANGES);
resultat;
