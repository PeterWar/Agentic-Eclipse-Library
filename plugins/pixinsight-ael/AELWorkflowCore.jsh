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

// The engine writes how far it has gone into a small JSON file; each new step goes to the Console. Aborting the script
// from the Console leaves the file that stops the engine at its next step.
function aelWorkflowProgress( progressPath, cancelPath )
{
   let last = 0;
   let said = "";
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
      }
   };
}

// RAW photos of the totality in, and, if there are any, darks and flats (mixed: AEL tells them apart). AEL measures the
// rest (camera, levels, the Moon, the registration on the Sun, colour) and makes the linear master and its default
// filter layers, which open here with their PixelMath composite. The same photos give the same master and layers as in
// the Photoshop connector. A run that stops leaves no empty folder behind.
function aelWorkflowRaw( raw, calibration, outputRoot, pythonPath, aelRoot, buildComposite )
{
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
      File.writeTextFile( configPath, JSON.stringify( { raw: raw, calibration: calibration, out: output,
                                                        progress: progressPath, cancel: cancelPath }, null, 1 ) );
      console.show();
      Console.writeln( "AEL: " + raw.length + " RAW photos and " + calibration.length + " darks and flats, into " + output );
      let result = aelWorkflowRunAndOpen( "raw", configPath, runtime, aelRoot, buildComposite,
                                          aelWorkflowProgress( progressPath, cancelPath ) );
      let s = result.summary;
      let left = result.left_out || [];
      Console.noteln( "AEL: " + s.frames_stacked + " of " + s.frames_chosen + " photos stacked into one image ("
                      + s.camera + ", " + s.date + "), saved with its layers and a receipt in " + result.out );
      for ( let i = 0; i < left.length; ++i )
         Console.warningln( "Left out: " + left[i].file + ": " + left[i].reason );
      if ( s.cloudy )
         Console.warningln( "The sky changed during the totality (thin clouds or haze): faint arcs may show where an "
                            + "exposure saturates." );
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
function aelWorkflowFiltersFromView( view, outputRoot, filters, pythonPath, aelRoot, buildComposite )
{
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
                     filters: filters };
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
