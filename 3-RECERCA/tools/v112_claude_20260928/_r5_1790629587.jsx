#target photoshop
function jaObert(f) { for (var i = 0; i < app.documents.length; i++) { if (app.documents[i].name == f.name) return true; } return false; }  // ⛔ 28-09: mai reutilitzar ni tancar un document que Pere tingui obert
// r5 · render natiu (Claude, V113): obre 1-PHOTOSHOP/V114.psb, amaga les capes 202 i desa el visible complet (TIFF sense compressió) i el llenç a 2400 px a 4-RESULTATS/v114_estrelles_20260928/renders/V114_sense_estrelles.
// No desa el PSB ni toca cap altre document obert.
var ROOT = new File($.fileName).parent.parent.parent.parent;
var SRC = new File(ROOT.fsName + '/1-PHOTOSHOP/V114.psb'), DIR = new Folder(ROOT.fsName + '/4-RESULTATS/v114_estrelles_20260928/renders/V114_sense_estrelles'), HIDE = [202];
if (!DIR.exists) DIR.create();
var prior = app.documents.length ? app.activeDocument : null, dialogs = app.displayDialogs, units = app.preferences.rulerUnits, d = null;
function log(s) { var f = new File(DIR.fsName + '/RENDER.log'); f.encoding = 'UTF-8'; f.open('a'); f.writeln(new Date().toUTCString() + ' ' + s); f.close(); }
function vista(name, w) { app.activeDocument = d; var x = d.duplicate('V113_' + name, true);
  try { if (w) x.resizeImage(UnitValue(w, 'px'), null, null, ResampleMethod.BICUBIC); var t = new TiffSaveOptions(); t.layers = false; t.alphaChannels = false; t.embedColorProfile = true; t.imageCompression = TIFFEncoding.NONE;
    var f = new File(DIR.fsName + '/' + name + '.tif'); if (f.exists) throw Error('Existeix ' + f); x.saveAs(f, t, true, Extension.LOWERCASE);
  } finally { x.close(SaveOptions.DONOTSAVECHANGES); } log('VISTA ' + name); }
try { app.displayDialogs = DialogModes.NO; app.preferences.rulerUnits = Units.PIXELS;
  if (jaObert(SRC)) throw Error('OBERT_PER_PERE: ' + SRC.name + ' ja és obert al Photoshop; no el toco'); d = app.open(SRC);
  for (var k = 0; k < HIDE.length; k++) { var found = 0; for (var i = 0; i < d.layers.length; i++) if (d.layers[i].id == HIDE[k]) { d.layers[i].visible = false; found++; } if (found != 1) throw Error('No layer ' + HIDE[k]); }
  var v = d.layers[0].visible; d.layers[0].visible = !v; d.layers[0].visible = v; app.refresh(); var hist = d.histogram;
  log('OBRE ' + d.name + ' capes ' + d.layers.length + ' amagades ' + HIDE.join(',')); vista('visible_complet', null); vista('llenc_sencer', 2400); log('COMPLET');
} catch (e) { log('ERROR ' + e + ' line ' + e.line); throw e; }
finally { if (d) d.close(SaveOptions.DONOTSAVECHANGES); if (prior) app.activeDocument = prior; app.displayDialogs = dialogs; app.preferences.rulerUnits = units; }
'R5_RENDER_FET';
