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

function aelWorkflowExecute( operation, configPath, runtime, aelRoot )
{
   if ( !File.exists( AEL_WORKFLOW_SCRIPT ) )
      throw new Error( "Workflow helper not found: " + AEL_WORKFLOW_SCRIPT );
   let run = aelBridgeRun( runtime.python, [ AEL_WORKFLOW_SCRIPT, operation, configPath ],
                           aelRoot && aelRoot.length ? aelRoot : File.systemTempDirectory,
                           aelBridgeEnvironment( aelRoot ), 1800000 );
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

function aelWorkflowRunAndOpen( operation, configPath, runtime, aelRoot, buildComposite )
{
   let result = aelWorkflowExecute( operation, configPath, runtime, aelRoot );
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
            result.windows.push( aelBridgeShowGeometryCheck( View.viewById( displayId ), result.geometry,
                                                             { low: 0, high: 1 } ) );
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

#endif // __AEL_WORKFLOW_CORE_jsh
