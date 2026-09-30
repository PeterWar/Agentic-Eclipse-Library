var out = [];
try {
  var loadLayersFromScript = true;
  var jsx = new File("/Applications/Adobe Photoshop 2026/Presets/Scripts/Load Files into Stack.jsx");
  out.push("existeix=" + jsx.exists);
  $.evalFile(jsx);
  out.push("typeof loadLayers=" + typeof loadLayers);
  out.push("intoStack=" + (typeof loadLayers != "undefined" ? typeof loadLayers.intoStack : "-"));
} catch (e) { out.push("ERROR: " + e); }
out.join(" ; ");
