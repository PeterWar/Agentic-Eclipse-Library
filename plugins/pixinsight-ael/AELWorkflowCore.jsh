/*
 * MIT License
 * Copyright (c) 2026 Pere Guerra Serra
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 * Processed with Agentic Eclipse Library by Pere Guerra —
 * https://github.com/PeterWar/Agentic-Eclipse-Library
 */

#ifndef __AEL_WORKFLOW_CORE_jsh
#define __AEL_WORKFLOW_CORE_jsh

#include "AELBridgeCore.jsh"
#include <pjsr/SampleType.jsh>
#include <pjsr/ColorSpace.jsh>
#include <pjsr/UndoFlag.jsh>

var AEL_WORKFLOW_SCRIPT = AEL_BRIDGE_CORE_DIR + "/python/ael_workflow.py";
// A whole totality with its darks and flats can take long: the RAW workflow has hours, and aborting from the Console
// stops it at its next step.
var AEL_RAW_TIME_LIMIT_MS = 4 * 3600 * 1000;
// While the engine works without a new step to report (one filter can take minutes), the Console still hears from it.
var AEL_HEARTBEAT_MS = 20000;
// Where the whole library is, for the line that invites people to use it with an AI agent.
var AEL_GITHUB_URL = "https://github.com/PeterWar/Agentic-Eclipse-Library";
// The licence of the library and of this connector (LICENSE): one line under the invitation, and the whole disclaimer
// when the pointer rests on it.
var AEL_LICENCE_LINE = "MIT License \u00b7 Copyright \u00a9 2026 Pere Guerra Serra \u00b7 Provided \u201cas is\u201d, "
                     + "without warranty of any kind.";
var AEL_LICENCE_DISCLAIMER = "THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, "
                           + "INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR "
                           + "PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE "
                           + "FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR "
                           + "OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER "
                           + "DEALINGS IN THE SOFTWARE.";

// AEL's filters, as the library names them (ael.filterbank.NAMES, ael.develop.layer_names): the layer's name, its blend
// mode in the composite, its opacity there (AEL's three default layers; 0 opens the layer without composing it) and
// what it shows. tests/validate.py checks this list against the library that comes with the connector.
var AEL_FILTERS = [
   { name: "nrgf", label: "01 NRGF", mode: "Multiply", opacity: 0.39,
     about: "Normalising radial graded filter: each radius scaled by its own spread, so the corona's shape shows from the "
            + "limb outwards." },
   { name: "nrgf_log", label: "01 NRGF log", mode: "Multiply", opacity: 0,
     about: "The NRGF on the logarithm of the brightness: softer in the bright inner corona." },
   { name: "rhef", label: "02 RHEF", mode: "Multiply", opacity: 0,
     about: "Radial histogram equalisation: each radius spread over the whole tonal range." },
   { name: "rhef_upsilon", label: "02 RHEF Upsilon", mode: "Multiply", opacity: 0,
     about: "Radial histogram equalisation with the Upsilon curve, gentler at both ends." },
   { name: "rhef_local60", label: "02 RHEF local 60°", mode: "Multiply", opacity: 0,
     about: "Radial histogram equalisation in sectors of 60 degrees: each sector against its own range." },
   { name: "rhef_local30", label: "02 RHEF local 30°", mode: "Multiply", opacity: 0,
     about: "Radial histogram equalisation in sectors of 30 degrees." },
   { name: "mgn", label: "03 MGN", mode: "Overlay", opacity: 0,
     about: "Multi-scale Gaussian normalisation (Morgan and Druckmüller): fine structure at every scale." },
   { name: "achf_angular", label: "04 ACHF angular", mode: "Overlay", opacity: 0,
     about: "Angular high-pass: detail across the rays, along the position angle." },
   { name: "achf_angular4", label: "04 ACHF angular smoothed 4 px", mode: "Overlay", opacity: 0,
     about: "Angular high-pass, smoothed over 4 pixels along the radius." },
   { name: "achf_angular8", label: "04 ACHF angular smoothed 8 px", mode: "Overlay", opacity: 0,
     about: "Angular high-pass, smoothed over 8 pixels along the radius." },
   { name: "achf_iso_01", label: "04 ACHF iso 2–32 px", mode: "Overlay", opacity: 0,
     about: "Isotropic high-pass of the detail between 2 and 32 pixels." },
   { name: "achf_iso_04", label: "04 ACHF iso 1–16 px", mode: "Overlay", opacity: 0.08,
     about: "Isotropic high-pass of the finest detail, 1 to 16 pixels." },
   { name: "achf_iso_05", label: "04 ACHF iso 2–48 px", mode: "Overlay", opacity: 0,
     about: "Isotropic high-pass of the detail between 2 and 48 pixels." },
   { name: "achf_iso_06", label: "04 ACHF iso 4–64 px", mode: "Overlay", opacity: 0,
     about: "Isotropic high-pass of the broader detail, 4 to 64 pixels." },
   { name: "wow", label: "05 WOW", mode: "Overlay", opacity: 0,
     about: "Wavelet-based detail at every scale, each scale against its own noise." },
   { name: "wow_edge_aware", label: "05 WOW edge-aware", mode: "Overlay", opacity: 0.37,
     about: "Wavelet-based detail that keeps the edges of the structure sharp." }
];

// AEL's default layers in the order the engine and the Photoshop connector stack them (ael.filterbank.DEFAULTS): the
// composite applies its layers one after another, and Overlay does not commute.
var AEL_DEFAULT_ORDER = [ "nrgf", "wow_edge_aware", "achf_iso_04" ];

// The filters chosen, in the order they are stacked: AEL's default ones first, in their order, then the others as listed.
function aelWorkflowOrdered( names )
{
   let ordered = AEL_DEFAULT_ORDER.filter( function( name ) { return names.indexOf( name ) >= 0; } );
   for ( let i = 0; i < AEL_FILTERS.length; ++i )
      if ( names.indexOf( AEL_FILTERS[i].name ) >= 0 && ordered.indexOf( AEL_FILTERS[i].name ) < 0 )
         ordered.push( AEL_FILTERS[i].name );
   return ordered;
}

// The filters a run makes: AEL's three default layers at their opacities, unless the advanced settings chose others.
function aelWorkflowDefaultFilters()
{
   let choice = { filters: AEL_DEFAULT_ORDER.slice(), opacities: {} };
   for ( let i = 0; i < AEL_FILTERS.length; ++i )
      if ( AEL_DEFAULT_ORDER.indexOf( AEL_FILTERS[i].name ) >= 0 )
         choice.opacities[AEL_FILTERS[i].name] = AEL_FILTERS[i].opacity;
   return choice;
}

// The RAW workflow is the engine the Photoshop connector shares (python/ael_auto.py), reached through the bridge's
// helper; the filter layers of an open image go through the workflow helper.
function aelWorkflowExecute( operation, configPath, runtime, aelRoot, onWait )
{
   let raw = operation == "raw";
   let script = raw ? AEL_BRIDGE_CHECK_SCRIPT : AEL_WORKFLOW_SCRIPT;
   if ( !File.exists( script ) )
      throw new Error( "Workflow helper not found: " + script );
   let run = aelBridgeRun( runtime.python, [ script, operation, configPath ],
                           aelRoot && aelRoot.length ? aelRoot : File.systemTempDirectory,
                           aelBridgeEnvironment( aelRoot ), raw ? AEL_RAW_TIME_LIMIT_MS : 1800000, onWait );
   if ( run.timedOut )
      throw new Error( "The AEL workflow exceeded its time limit and was stopped." );
   if ( !run.ok )
      throw new Error( "AEL workflow process failed:\n" + run.stderr + "\n" + run.stdout );
   let result = aelBridgeParseJson( run.stdout, "AEL workflow" );
   if ( !result.ok )
      throw new Error( result.message || "AEL workflow failed" );
   return result;
}

function aelWorkflowOpenImages( result )
{
   result.windows = [];
   result.idMap = {};
   let stamp = aelBridgeTimestamp();
   for ( let i = 0; i < result.images.length; ++i )
   {
      let item = result.images[i];
      let id = aelBridgeId( item.view );
      let existing = View.viewById( id );
      if ( existing && !existing.isNull )
         id = aelBridgeId( id + "_" + stamp );
      let windows = ImageWindow.open( item.path, id );
      if ( windows == null || windows.length != 1 )
         throw new Error( "Could not open workflow image: " + item.path );
      windows[0].show();
      result.windows.push( windows[0] );
      result.idMap[item.view] = windows[0].mainView.id;
      item.actualView = windows[0].mainView.id;
   }
   return result;
}

function aelWorkflowExpression( operation, layerId, alphaId )
{
   // PixelMath symbols take constants only; view identifiers go into the expression.
   let weight = "(" + alphaId + "*" + operation.effective_opacity + ")";
   if ( operation.mode == "normal" )
      return { symbols: "", expression: "$T*(1-" + weight + ")+" + layerId + "*" + weight };
   if ( operation.mode == "multiply" )
      return { symbols: "", expression: "$T*(1-" + weight + ")+$T*" + layerId + "*" + weight };
   if ( operation.mode == "overlay" )
      return { symbols: "",
               expression: "$T*(1-" + weight + ")+iif($T<=0.5,2*$T*" + layerId + ",1-2*(1-$T)*(1-"
                           + layerId + "))*" + weight };
   throw new Error( "Unsupported PixelMath blend mode: " + operation.mode );
}

function aelWorkflowBuildComposite( result )
{
   if ( !result.pixelmath || result.pixelmath.length == 0 )
      return null;
   let displayId = result.idMap["AEL_DISPLAY"];
   if ( !displayId )
      throw new Error( "The display base is not available for the composite" );
   let display = View.viewById( displayId );
   let compositeId = aelBridgeId( "AEL_COMPOSITE_" + aelBridgeTimestamp() );
   // 32-bit float: a 16-bit integer target would round after every PixelMath step.
   let compositeWindow = new ImageWindow( display.image.width, display.image.height,
      display.image.numberOfChannels, 32, true, display.image.isColor, compositeId );
   let composite = compositeWindow.mainView;
   composite.beginProcess( UndoFlag.NoSwapFile );
   composite.image.assign( display.image );
   composite.endProcess();
   compositeWindow.show();
   result.windows.push( compositeWindow );
   result.composite = composite;

   for ( let i = 0; i < result.pixelmath.length; ++i )
   {
      let operation = result.pixelmath[i];
      let layerId = result.idMap[operation.layer_view];
      let alphaId = result.idMap[operation.alpha_view];
      if ( !layerId || !alphaId )
         throw new Error( "Missing layer or alpha view for " + operation.filter );
      let recipe = aelWorkflowExpression( operation, layerId, alphaId );
      let process = new PixelMath;
      process.expression = recipe.expression;
      process.symbols = recipe.symbols;
      process.useSingleExpression = true;
      process.clearImageCacheAndExit = false;
      process.cacheGeneratedImages = false;
      process.generateOutput = true;
      process.singleThreaded = false;
      process.optimization = true;
      process.rescale = false;
      process.truncate = false;
      process.createNewImage = false;
      if ( !process.executeOn( composite ) )
         throw new Error( "PixelMath failed for " + operation.filter + ": " + recipe.expression );
      Console.writeln( "PixelMath " + operation.filter + ": " + recipe.expression );
   }
   return composite;
}

// Where the composite is saved: beside the run's preview, with its name (Eclipse … composite.xisf), or in the run's
// folder.
function aelWorkflowCompositePath( result )
{
   if ( result.preview && /preview\.png$/.test( result.preview ) )
      return result.preview.replace( /preview\.png$/, "composite.xisf" );
   return result.out ? result.out + "/AEL composite.xisf" : null;
}

function aelWorkflowRunAndOpen( operation, configPath, runtime, aelRoot, buildComposite, onWait )
{
   let result = aelWorkflowExecute( operation, configPath, runtime, aelRoot, onWait );
   try
   {
      aelWorkflowOpenImages( result );
      if ( buildComposite )
         aelWorkflowBuildComposite( result );
      // A geometry that AEL measured is shown for checking: its circles drawn over the display base, in a new window.
      if ( result.geometry && result.geometry_source && result.geometry_source != "given" )
      {
         Console.writeln( "AEL workflow: geometry " + result.geometry_source + ": " + result.geometry.note );
         let displayId = result.idMap["AEL_DISPLAY"];
         if ( displayId )
            result.windows.push( aelBridgeShowGeometryCheck( View.viewById( displayId ), result.geometry ) );
      }
      // The composite is the result: saved with the rest (32-bit XISF) and shown in front of the other windows.
      if ( result.composite )
      {
         let path = aelWorkflowCompositePath( result );
         if ( path )
         {
            if ( !result.composite.window.saveAs( path, false, false, false, false ) )
               throw new Error( "Could not save the composite: " + path );
            result.compositePath = path;
            Console.writeln( "AEL workflow: composite saved in " + path );
         }
         result.composite.window.bringToFront();
      }
      Console.writeln( "AEL workflow receipt: " + result.receipt );
      Console.writeln( File.readTextFile( result.receipt ) );
      return result;
   }
   catch ( error )
   {
      if ( result.windows )
         for ( let i = 0; i < result.windows.length; ++i )
            result.windows[i].forceClose();
      throw error;
   }
}

// A folder name that does not exist yet under root (the helper refuses an existing one); root is created if needed.
function aelWorkflowNewOutput( root, kind )
{
   if ( !File.directoryExists( root ) )
      File.createDirectory( root, true );
   let base = root + "/ael_" + kind + "_" + aelBridgeTimestamp();
   let output = base;
   let suffix = 1;
   while ( File.exists( output ) || File.directoryExists( output ) )
      output = base + "_" + String( ++suffix );
   return output;
}

// The folder of one RAW run, named as the Photoshop connector names its own: the prefix, then the local date and time
// (AEL_20261031_031502_7), and _1, _2… after it if that name is taken. The engine creates it; root is created if needed.
function aelWorkflowStampedOutput( root, prefix )
{
   if ( !File.directoryExists( root ) )
      File.createDirectory( root, true );
   let now = new Date();
   let two = function( n ) { return n < 10 ? "0" + n : String( n ); };
   let base = root + "/" + prefix + now.getFullYear() + two( now.getMonth() + 1 ) + two( now.getDate() ) + "_"
              + two( now.getHours() ) + two( now.getMinutes() ) + two( now.getSeconds() ) + "_" + now.getMilliseconds();
   let output = base;
   for ( let suffix = 1; File.exists( output ) || File.directoryExists( output ); ++suffix )
      output = base + "_" + suffix;
   return output;
}

// The engine writes how far it has gone into a small JSON file; each new step goes to the Console, and while a step lasts
// a line every AEL_HEARTBEAT_MS says that it is still working. Aborting the script from the Console leaves the file that
// stops the engine at its next step.
function aelWorkflowProgress( progressPath, cancelPath )
{
   let last = 0;
   let said = "";
   let saidAt = Date.now();
   console.abortEnabled = true;
   return function()
   {
      let now = Date.now();
      if ( now - last < 500 )
         return;
      last = now;
      if ( console.abortRequested && !File.exists( cancelPath ) )
      {
         File.writeTextFile( cancelPath, "stop" );
         Console.warningln( "AEL: stopping at the next step…" );
      }
      if ( !File.exists( progressPath ) )
         return;
      let info;
      try { info = JSON.parse( File.readTextFile( progressPath ) ); } catch ( busy ) { return; }
      let text = info.stage + ( info.total ? " (" + info.done + " of " + info.total + ")" : "" )
                 + ( info.message ? ": " + info.message : "" );
      if ( text != said )
      {
         Console.writeln( "AEL: " + text + " — " + Math.round( info.elapsed_s || 0 ) + " s" );
         Console.flush();
         said = text;
         saidAt = now;
      }
      else if ( now - saidAt >= AEL_HEARTBEAT_MS )
      {
         Console.writeln( "AEL: still working on " + text + " — " + Math.round( ( now - saidAt ) / 1000 ) + " s more" );
         Console.flush();
         saidAt = now;
      }
   };
}

// RAW photos of the totality in, and, if there are any, darks and flats (AEL still measures each and leaves out one that
// is not what it was chosen as). AEL measures the rest (camera, levels, the Moon, the registration on the Sun, colour)
// and makes the linear master and its filter layers (``choice``: the filters and their opacities; AEL's default layers
// when there is none), which open here with their PixelMath composite. The same photos give the same master and layers
// as in the Photoshop connector. A run that stops leaves no empty folder behind.
function aelWorkflowRaw( raw, darks, flats, outputRoot, pythonPath, aelRoot, buildComposite, choice )
{
   choice = choice || aelWorkflowDefaultFilters();
   let runtime = aelBridgeCandidates( pythonPath, aelRoot );
   if ( !runtime.ok )
      throw new Error( runtime.message || "Python preflight failed." );
   Settings.write( AEL_BRIDGE_SETTINGS_KEY + "pythonPath", DataType.UTF8String, runtime.python );
   let tempDir = File.systemTempDirectory + "/pixinsight-ael-" + aelBridgeTimestamp();
   File.createDirectory( tempDir, false );
   let configPath = tempDir + "/raw.json";
   let progressPath = tempDir + "/progress.json";
   let cancelPath = tempDir + "/cancel";
   let temporaryFiles = [ configPath, progressPath, tempDir + "/progress.tmp", cancelPath ];
   let output = aelWorkflowStampedOutput( outputRoot, "AEL_" );
   try
   {
      File.writeTextFile( configPath, JSON.stringify( { raw: raw, darks: darks, flats: flats, out: output,
                                                        filters: choice.filters, opacities: choice.opacities,
                                                        progress: progressPath, cancel: cancelPath }, null, 1 ) );
      console.show();
      Console.writeln( "AEL: " + raw.length + " RAW photos, " + darks.length + " darks and " + flats.length
                       + " flats, into " + output );
      let result = aelWorkflowRunAndOpen( "raw", configPath, runtime, aelRoot, buildComposite,
                                          aelWorkflowProgress( progressPath, cancelPath ) );
      Console.noteln( aelWorkflowDoneMessage( result ) );
      return result;
   }
   catch ( error )
   {
      if ( File.directoryExists( output ) && aelWorkflowEmptyFolder( output ) )
         try { File.removeDirectory( output ); } catch ( busy ) {}
      throw error;
   }
   finally
   {
      aelBridgeCleanup( tempDir, temporaryFiles );
   }
}

// What a RAW run did, as the Photoshop connector says it when it finishes: how many photos were stacked, which were left
// out and why, and where everything was saved.
function aelWorkflowDoneMessage( result )
{
   let s = result.summary;
   let left = result.left_out || [];
   let text = "Done: " + s.frames_stacked + " of " + s.frames_chosen + " photos stacked into one image ("
              + s.camera + ", " + s.date + ").";
   if ( left.length )
   {
      text += "\n\nLeft out (" + left.length + "):";
      for ( let i = 0; i < Math.min( left.length, 5 ); ++i )
         text += "\n• " + left[i].file + ": " + left[i].reason;
      if ( left.length > 5 )
         text += "\n• … and " + ( left.length - 5 ) + " more, listed in the receipt";
   }
   if ( s.cloudy )
      text += "\n\nThe sky changed during the totality (thin clouds or haze): faint arcs may show where an exposure "
              + "saturates.";
   text += "\n\nThe linear master, its filter layers and their PixelMath composite are open. They are saved, "
           + "with a receipt, in:\n" + result.out;
   let scale = result.linear_master_scale;
   if ( scale )
      text += "\n\nThe linear master holds DN per second" + ( scale.offset_dn_per_s ? " plus " + ( -scale.offset_dn_per_s ) : "" )
              + ", divided by " + scale.unit_dn_per_s + "; where nothing was observed it is transparent.";
   return text + "\n\nFor more faithful results and more filters, try the whole Agentic Eclipse Library with an AI "
          + "agent: " + AEL_GITHUB_URL;
}

function aelWorkflowEmptyFolder( folder )
{
   let find = new FileFind;
   let empty = true;
   for ( let more = find.begin( folder + "/*" ); more && empty; more = find.next() )
      if ( find.name != "." && find.name != ".." )
         empty = false;
   find.end();
   return empty;
}

// AEL's filter layers from an open image. The image is handed to AEL as the bridge hands it (exported to a temporary
// 32-bit TIFF with its samples without data put back as NaN, or the file itself when PixInsight does not hold it as
// stored); the image is not changed and the temporary files are removed. AEL measures the geometry on the image, as for
// the structure image: a geometry.json that happens to lie beside the file is not taken.
function aelWorkflowFiltersFromView( view, outputRoot, choice, pythonPath, aelRoot, buildComposite )
{
   choice = choice || aelWorkflowDefaultFilters();
   let runtime = aelBridgeCandidates( pythonPath, aelRoot );
   if ( !runtime.ok )
      throw new Error( runtime.message || "Python preflight failed." );
   Settings.write( AEL_BRIDGE_SETTINGS_KEY + "pythonPath", DataType.UTF8String, runtime.python );
   let tempDir = File.systemTempDirectory + "/pixinsight-ael-" + aelBridgeTimestamp();
   File.createDirectory( tempDir, false );
   let configPath = tempDir + "/filters.json";
   let temporaryFiles = [ configPath ];
   try
   {
      let prepared = aelBridgePrepareInput( view, runtime, aelRoot, tempDir, temporaryFiles );
      let config = { input: prepared.inputPath, geometry: "auto", out: aelWorkflowNewOutput( outputRoot, "filters" ),
                     filters: choice.filters, opacities: {}, visible: [] };
      // the layers with an opacity enter the composite; the others open on their own
      for ( let i = 0; i < choice.filters.length; ++i )
         if ( ( choice.opacities[choice.filters[i]] || 0 ) > 0 )
         {
            config.visible.push( choice.filters[i] );
            config.opacities[choice.filters[i]] = choice.opacities[choice.filters[i]];
         }
      File.writeTextFile( configPath, JSON.stringify( config, null, 1 ) );
      Console.writeln( "AEL filter layers of " + view.id + ( prepared.onFile ? " (AEL reads its file)" : "" ) );
      return aelWorkflowRunAndOpen( "filters", configPath, runtime, aelRoot, buildComposite );
   }
   finally
   {
      aelBridgeCleanup( tempDir, temporaryFiles );
   }
}

#endif // __AEL_WORKFLOW_CORE_jsh
