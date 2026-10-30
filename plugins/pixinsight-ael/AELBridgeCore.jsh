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

#ifndef __AEL_BRIDGE_CORE_jsh
#define __AEL_BRIDGE_CORE_jsh

#include <pjsr/DataType.jsh>
#include <pjsr/StdButton.jsh>
#include <pjsr/StdIcon.jsh>

var AEL_BRIDGE_SETTINGS_KEY = "AELBridge/";
var AEL_BRIDGE_CREDIT = "Processed with Agentic Eclipse Library by Pere Guerra — https://github.com/PeterWar/Agentic-Eclipse-Library";

// PixInsight expands #__FILE__ with every non-ASCII character of the path replaced by U+FFFD, so File.exists() fails for a
// connector installed under, say, "Descàrregues" or "Música". The real path is recovered by listing each folder whose name
// is damaged and taking the entry that fits it, each U+FFFD standing for one to three characters (an accent can be one
// character or two). If nothing fits, the damaged path is kept and the error that follows says what happened.
function aelBridgeRepairPath( damaged )
{
   let broken = String.fromCharCode( 0xFFFD );
   if ( damaged.indexOf( broken ) < 0 )
      return damaged;
   let parts = damaged.split( "/" );
   let repaired = parts[0];
   for ( let i = 1; i < parts.length; ++i )
   {
      if ( parts[i].indexOf( broken ) < 0 )
      {
         repaired += "/" + parts[i];
         continue;
      }
      let source = "^";
      for ( let j = 0; j < parts[i].length; ++j )
      {
         let character = parts[i].charAt( j );
         source += character == broken ? ".{1,3}" : character.replace( /[.*+?^${}()|[\]\\]/g, "\\$&" );
      }
      let pattern = new RegExp( source + "$" );
      let fitting = [];
      let entries = aelBridgeMatches( repaired + "/*" );
      for ( let k = 0; k < entries.length; ++k )
         if ( pattern.test( File.extractName( entries[k] ) + File.extractExtension( entries[k] ) ) )
            fitting.push( entries[k] );
      if ( fitting.length == 0 )
         return damaged;
      fitting.sort();
      repaired = fitting[0];
   }
   return repaired;
}

var AEL_BRIDGE_CORE_DIR = aelBridgeRepairPath( File.extractDrive( #__FILE__ ) + File.extractDirectory( #__FILE__ ) );
var AEL_BRIDGE_CHECK_SCRIPT = AEL_BRIDGE_CORE_DIR + "/python/ael_bridge_check.py";

function aelBridgeTimestamp()
{
   let d = new Date();
   function pad( n ) { return n < 10 ? "0" + n : String( n ); }
   return String( d.getUTCFullYear() ) + pad( d.getUTCMonth() + 1 ) + pad( d.getUTCDate() )
          + "_" + pad( d.getUTCHours() ) + pad( d.getUTCMinutes() ) + pad( d.getUTCSeconds() )
          + "_" + String( d.getUTCMilliseconds() );
}

function aelBridgeId( text )
{
   let id = String( text ).replace( /[^A-Za-z0-9_]/g, "_" );
   if ( id.length == 0 || !id.charAt( 0 ).match( /[A-Za-z_]/ ) )
      id = "AEL_" + id;
   return id;
}

function aelBridgeParseJson( text, context )
{
   let begin = text.indexOf( "{" );
   let end = text.lastIndexOf( "}" );
   if ( begin < 0 || end < begin )
      throw new Error( context + " did not return a JSON object.\n" + text );
   try
   {
      return JSON.parse( text.substring( begin, end + 1 ) );
   }
   catch ( error )
   {
      throw new Error( context + " returned invalid JSON: " + error + "\n" + text );
   }
}

function aelBridgeEnvironment( aelRoot )
{
   let environment = [ "PYTHONDONTWRITEBYTECODE=1" ];
   if ( aelRoot && aelRoot.trim().length > 0 )
      environment.push( "PYTHONPATH=" + aelRoot.trim() );
   return environment;
}

function aelBridgeRun( program, arguments, workingDirectory, environment, timeoutMs )
{
   let process = new ExternalProcess;
   let stdout = "";
   let stderr = "";
   let startError = "";
   let timedOut = false;

   process.onError = function( code ) { startError = String( code ); };
   process.onStandardOutputDataAvailable = function() { stdout += this.stdout.utf8ToString(); };
   process.onStandardErrorDataAvailable = function() { stderr += this.stderr.utf8ToString(); };
   process.environment = environment || [];
   if ( workingDirectory && workingDirectory.length > 0 )
      process.workingDirectory = workingDirectory;

   if ( !process.start( program, arguments ) )
      return { ok: false, exitCode: -1, stdout: stdout, stderr: stderr,
               error: "Could not start " + program + (startError.length ? " (error " + startError + ")" : "") };

   let started = Date.now();
   while ( process.isStarting || process.isRunning )
   {
      CoreApplication.processEvents();
      if ( timeoutMs > 0 && Date.now() - started > timeoutMs )
      {
         timedOut = true;
         process.kill();
         process.waitForFinished( 5000 );
         break;
      }
   }
   stdout += process.standardOutput.utf8ToString();
   stderr += process.standardError.utf8ToString();
   return { ok: !timedOut && process.exitCode == 0, exitCode: process.exitCode,
            stdout: stdout, stderr: stderr, timedOut: timedOut, error: "" };
}

function aelBridgeProbe( pythonPath, aelRoot )
{
   if ( !pythonPath || pythonPath.trim().length == 0 )
      return { ok: false, kind: "bad_path", message: "No Python interpreter was specified." };
   if ( !File.exists( pythonPath ) )
      return { ok: false, kind: "bad_path", message: "Python executable not found: " + pythonPath };
   if ( !File.exists( AEL_BRIDGE_CHECK_SCRIPT ) )
      throw new Error( "Bridge preflight helper not found: " + AEL_BRIDGE_CHECK_SCRIPT + "\n\nKeep the connector's folder "
                       + "together. If the path of the folder holds accented or special characters that PixInsight cannot "
                       + "read in a script's location, move the folder to a plain path." );

   let run = aelBridgeRun( pythonPath, [ AEL_BRIDGE_CHECK_SCRIPT, "probe" ],
                           aelRoot && aelRoot.length ? aelRoot : File.systemTempDirectory,
                           aelBridgeEnvironment( aelRoot ), 20000 );
   if ( !run.ok )
      return { ok: false, kind: "bad_path", message: "Python preflight failed: " + run.error + "\n" + run.stderr };
   let result = aelBridgeParseJson( run.stdout, "Python preflight" );
   result.python = pythonPath;
   return result;
}

// Files, links and folders that match a wildcard in the last component of ``pattern``; none if the folder does
// not exist. (searchDirectory() lists files only, so it would never see a virtual-environment folder.)
function aelBridgeMatches( pattern )
{
   let found = [];
   let finder = new FileFind;
   try
   {
      let directory = File.extractDrive( pattern ) + File.extractDirectory( pattern );
      if ( finder.begin( pattern ) )
         do
         {
            if ( finder.name != "." && finder.name != ".." )
               found.push( directory + "/" + finder.name );
         }
         while ( finder.next() );
   }
   catch ( error )
   {
   }
   finally
   {
      try { finder.end(); } catch ( error ) {}
   }
   return found;
}

// python3, then python3.N from the newest minor version to the oldest, in one folder.
function aelBridgeVersionedPythons( directory )
{
   function minor( path )
   {
      let match = /python3\.([0-9]+)$/.exec( path );
      return match ? parseInt( match[1] ) : 1000;
   }
   let list = aelBridgeMatches( directory + "/python3*" ).filter(
      function( path ) { return /\/python3(\.[0-9]+)?$/.test( path ); } );
   list.sort( function( a, b ) { return minor( b ) - minor( a ); } );
   return list;
}

// The folder that holds the ``ael`` package that comes with the connector: ``runtime`` beside the scripts (the ZIP),
// or the root of the repository that contains ``plugins/pixinsight-ael`` (a source checkout). Empty if neither.
function aelBridgeDefaultRoot()
{
   let runtime = AEL_BRIDGE_CORE_DIR + "/runtime";
   if ( File.exists( runtime + "/ael/__init__.py" ) )
      return runtime;
   let repository = File.extractDrive( AEL_BRIDGE_CORE_DIR ) + File.extractDirectory( File.extractDirectory( AEL_BRIDGE_CORE_DIR ) );
   if ( File.exists( repository + "/ael/__init__.py" ) )
      return repository;
   return "";
}

// The AEL folder a dialog starts with. The AEL that comes with the connector wins: a package is self-contained, and a
// folder saved by an earlier run (another package, an older checkout) would make a new package start with an AEL that
// is not its own. Only when the connector carries none, the one saved last time is used if it still holds ``ael``.
// Choosing another folder in the dialog still works for that run.
function aelBridgeInitialRoot()
{
   let packaged = aelBridgeDefaultRoot();
   if ( packaged.length > 0 )
      return packaged;
   let saved = Settings.read( AEL_BRIDGE_SETTINGS_KEY + "aelRoot", DataType.UTF8String );
   if ( saved && saved.length > 0 && File.exists( saved + "/ael/__init__.py" ) )
      return saved;
   return "";
}

function aelBridgeCandidates( preferred, aelRoot )
{
   let candidates = [];
   function add( path )
   {
      if ( path && path.trim().length > 0 && candidates.indexOf( path ) < 0 )
         candidates.push( path );
   }
   function addAll( paths )
   {
      for ( let i = 0; i < paths.length; ++i )
         add( paths[i] );
   }
   add( preferred );
   let saved = Settings.read( AEL_BRIDGE_SETTINGS_KEY + "pythonPath", DataType.UTF8String );
   if ( saved )
      add( saved );
   try
   {
      add( getEnvironmentVariable( "AEL_PYTHON" ) );
   }
   catch ( error )
   {
   }
#ifeq __PI_PLATFORM__ MACOSX
   addAll( aelBridgeVersionedPythons( "/opt/homebrew/bin" ) );
   addAll( aelBridgeVersionedPythons( "/usr/local/bin" ) );
#endif
#ifeq __PI_PLATFORM__ LINUX
   addAll( aelBridgeVersionedPythons( "/usr/local/bin" ) );
   addAll( aelBridgeVersionedPythons( "/usr/bin" ) );
#endif
#ifeq __PI_PLATFORM__ MSWINDOWS
   add( "python" );
#endif
   // Virtual environments, one folder per environment: ~/.venvs/<name>/bin/python and the like.
   let environments = [ File.homeDirectory + "/.venvs", File.homeDirectory + "/.virtualenvs", File.homeDirectory + "/venvs" ];
   for ( let i = 0; i < environments.length; ++i )
   {
      let folders = aelBridgeMatches( environments[i] + "/*" );
      folders.sort();
      for ( let j = 0; j < folders.length; ++j )
         add( folders[j] + "/bin/python" );
   }
   add( File.homeDirectory + "/venv/bin/python" );
   add( File.homeDirectory + "/.venv/bin/python" );
   add( File.homeDirectory + "/.pyenv/shims/python" );
   add( File.homeDirectory + "/miniconda3/bin/python" );
   add( File.homeDirectory + "/anaconda3/bin/python" );
   add( File.homeDirectory + "/miniforge3/bin/python" );
   add( File.homeDirectory + "/mambaforge/bin/python" );
#ifeq __PI_PLATFORM__ MACOSX
   add( "/usr/bin/python3" );
#endif

   let diagnostics = [];
   for ( let i = 0; i < candidates.length; ++i )
   {
      let probe = aelBridgeProbe( candidates[i], aelRoot );
      if ( probe.ok )
      {
         probe.diagnostics = diagnostics;
         return probe;
      }
      diagnostics.push( candidates[i] + ": " + probe.message );
   }
   throw new Error( "No Python 3.10+ interpreter with AEL " + "1.3.6 or later and its dependencies was found. Select the "
                    + "Python executable and the AEL folder (the connector's runtime folder, or a source checkout).\n\n"
                    + "AEL is not on PyPI. Its dependencies are installed with: python -m pip install numpy scipy "
                    + "opencv-python-headless pillow tifffile imageio\n\n"
                    + "Tried:\n" + diagnostics.join( "\n" ) );
}

// PixInsight rescales a floating-point file whose values leave 0-1 to exactly 0-1 when it opens it, so the view is
// not the data in the file, and AEL does not give the same result on rescaled numbers (its structure image depends on
// the scale and on the zero). The range of the view's own TIFF file, as stored, or null when there is nothing to check:
// no file, another format, an integer file, or a file that cannot be read.
function aelBridgeSourceRange( runtime, aelRoot, view )
{
   let path = view.window.filePath;
   if ( !path || path.length == 0 || !File.exists( path ) )
      return null;
   let extension = File.extractExtension( path ).toLowerCase();
   if ( extension != ".tif" && extension != ".tiff" )
      return null;
   let run = aelBridgeRun( runtime.python, [ AEL_BRIDGE_CHECK_SCRIPT, "source-range", path ],
                           aelRoot && aelRoot.length ? aelRoot : File.systemTempDirectory,
                           aelBridgeEnvironment( aelRoot ), 300000 );
   if ( !run.ok )
      return null;
   let result = aelBridgeParseJson( run.stdout, "Source range" );
   return result.ok && result.kind == "range" ? result : null;
}

function aelBridgeReadSourceICC( view )
{
   let result = { profile: null, bytes: 0, origin: "none" };
   let path = view.window.filePath;
   if ( !path || !File.exists( path ) )
   {
      result.origin = "not available for an unsaved image";
      return result;
   }
   let format = new FileFormat( File.extractExtension( path ), true, false );
   if ( format.isNull || !format.canStoreICCProfiles )
   {
      result.origin = "source format does not expose ICC profiles";
      return result;
   }
   let file = new FileFormatInstance( format );
   let opened = false;
   try
   {
      file.open( path );
      opened = true;
      if ( file.iccProfile && file.iccProfile.length > 0 )
      {
         result.profile = new ByteArray( file.iccProfile );
         result.bytes = result.profile.length;
         result.origin = "source file";
      }
   }
   finally
   {
      if ( opened )
         file.close();
   }
   return result;
}

function aelBridgeExportFloat32( view, path )
{
   if ( !view || view.isNull || !view.isMainView )
      throw new Error( "Select a main image view before running the bridge." );
   if ( view.image.numberOfChannels != 1 && view.image.numberOfChannels != 3 )
      throw new Error( "Only monochrome and three-channel RGB images are supported." );

   let format = new FileFormat( ".tif", false, true );
   if ( format.isNull )
      throw new Error( "This PixInsight installation cannot write TIFF files." );
   let file = new FileFormatInstance( format );
   if ( file.isNull )
      throw new Error( "Could not initialize the TIFF writer." );

   let created = false;
   let icc = aelBridgeReadSourceICC( view );
   try
   {
      if ( !file.create( path ) )
         throw new Error( "Could not create temporary TIFF: " + path );
      created = true;
      let description = new ImageDescription;
      description.bitsPerSample = 32;
      description.ieeefpSampleFormat = true;
      description.embedICCProfile = true;
      description.embedRGBWS = false;
      description.embedDisplayFunction = false;
      description.embedProcessingHistory = false;
      description.embedThumbnail = false;
      if ( !file.setOptions( description ) )
         throw new Error( "The TIFF writer rejected 32-bit floating-point output." );
      if ( icc.profile )
         file.iccProfile = icc.profile;
      if ( !file.writeImage( view.image ) )
         throw new Error( "Could not write temporary TIFF: " + path );
   }
   finally
   {
      if ( created )
         file.close();
   }
   let iccSidecar = "";
   if ( icc.profile )
   {
      iccSidecar = path + ".icc";
      File.writeFile( iccSidecar, icc.profile );
   }
   return { sourceICCBytes: icc.bytes, iccOrigin: icc.origin, iccSidecar: iccSidecar,
            sourceICCHex: icc.profile ? icc.profile.toHex() : "" };
}

// One pass over the samples of a view: the positions of the non-finite ones (NaN and infinities) and the count, range
// and sum of the finite ones. A position is (row * width + column) * channels + channel, as numpy counts them in a
// (height, width, channels) array.
function aelBridgeScanView( view )
{
   let image = view.image;
   let width = image.width, height = image.height, channels = image.numberOfChannels;
   let rows = Math.max( 1, Math.floor( 4000000 / width ) );
   let buffer = new Float32Array( width * rows );
   let positions = new Uint32Array( 1 << 16 );
   let count = 0, finite = 0, minimum = Infinity, maximum = -Infinity, sum = 0;
   for ( let c = 0; c < channels; ++c )
      for ( let y = 0; y < height; y += rows )
      {
         let n = Math.min( rows, height - y );
         image.getSamples( buffer, new Rect( 0, y, width, y + n ), c );
         let base = y * width;
         for ( let i = 0, k = width * n; i < k; ++i )
         {
            let v = buffer[i];
            if ( v - v !== 0 )
            {
               if ( count == positions.length )
               {
                  let larger = new Uint32Array( positions.length * 2 );
                  larger.set( positions );
                  positions = larger;
               }
               positions[count++] = ( base + i ) * channels + c;
            }
            else
            {
               ++finite;
               sum += v;
               if ( v < minimum ) minimum = v;
               if ( v > maximum ) maximum = v;
            }
         }
      }
   return { nonFinite: count, positions: positions.slice( 0, count ), finite: finite,
            minimum: minimum, maximum: maximum, sum: sum };
}

// PixInsight keeps a NaN in the view but writes it to a TIFF as 1.0 (measured on a real stack of 12 million pixels:
// 253,851 NaN samples came out as 1.0 and every AEL product then differed from the one made from the file). AEL takes
// NaN as "no data", so the positions of the view's non-finite samples go to the helper, which puts them back as NaN
// in the temporary TIFF.
function aelBridgeWriteNonFinite( scan, path )
{
   if ( scan.nonFinite > 0 )
      File.writeFile( path, new ByteArray( scan.positions ) );
}

// A view that is still its file must hold what the file holds. PixInsight does not always read a floating-point TIFF
// faithfully: when its last sample is NaN (no data in the bottom-right corner, which a registered stack often has) it
// reads the whole image as zeros, and a file with values outside 0-1 is rescaled. Compares the count of the samples
// with and without data, the range and the sum, with the numbers the helper read from the file. Returns the
// differences, or an empty list.
function aelBridgeFileDifferences( file, scan )
{
   function close( a, b ) { return Math.abs( a - b ) <= 1e-5 * Math.max( Math.abs( a ), Math.abs( b ) ) + 1e-12; }
   let differences = [];
   if ( scan.nonFinite != file.nonfinite_samples )
      differences.push( "the file has " + file.nonfinite_samples + " samples without data (NaN) and the view has " + scan.nonFinite );
   if ( scan.finite != file.finite_samples )
      differences.push( "the file has " + file.finite_samples + " finite samples and the view has " + scan.finite );
   if ( scan.finite > 0 && file.finite_samples > 0 )
   {
      if ( !close( scan.minimum, file.minimum ) )
         differences.push( "the smallest value is " + file.minimum + " in the file and " + scan.minimum + " in the view" );
      if ( !close( scan.maximum, file.maximum ) )
         differences.push( "the largest value is " + file.maximum + " in the file and " + scan.maximum + " in the view" );
      if ( !close( scan.sum, file.finite_sum ) )
         differences.push( "the sum of the finite values is " + file.finite_sum + " in the file and " + scan.sum + " in the view" );
   }
   return differences;
}

// The size of the file against the size of the view; an empty text when they agree.
function aelBridgeFileShapeDifference( file, view )
{
   let image = view.image;
   let seen = image.numberOfChannels == 1 ? [ image.height, image.width ] : [ image.height, image.width, image.numberOfChannels ];
   let stored = file.shape.length == 3 && file.shape[2] == 1 ? [ file.shape[0], file.shape[1] ] : file.shape;
   return seen.join( "x" ) == stored.join( "x" ) ? "" : "the file is " + stored.join( "x" ) + " and the view " + seen.join( "x" );
}

function aelBridgeInspectInput( runtime, aelRoot, path, view, sourceICCBytes, iccSidecar, nonFinitePath )
{
   let arguments = [ AEL_BRIDGE_CHECK_SCRIPT, "inspect", path,
                     "--width", String( view.image.width ), "--height", String( view.image.height ),
                     "--channels", String( view.image.numberOfChannels ) ];
   if ( sourceICCBytes > 0 )
      arguments.push( "--require-icc" );
   if ( iccSidecar && iccSidecar.length > 0 )
      arguments.push( "--icc-source", iccSidecar );
   if ( nonFinitePath && nonFinitePath.length > 0 )
      arguments.push( "--nonfinite", nonFinitePath );
   let run = aelBridgeRun( runtime.python, arguments,
                           aelRoot && aelRoot.length ? aelRoot : File.systemTempDirectory,
                           aelBridgeEnvironment( aelRoot ), 60000 );
   if ( !run.ok )
      throw new Error( "TIFF preflight failed: " + run.error + "\n" + run.stderr );
   let result = aelBridgeParseJson( run.stdout, "TIFF preflight" );
   if ( !result.ok )
      throw new Error( result.message || "The temporary TIFF did not pass validation." );
   return result;
}

function aelBridgeValidateGeometry( geometry, view )
{
   if ( !geometry || !geometry.shape || geometry.shape.length != 2 )
      throw new Error( "Geometry must contain shape: [height, width]." );
   if ( geometry.shape[0] != view.image.height || geometry.shape[1] != view.image.width )
      throw new Error( "Geometry shape does not match the selected image." );
   if ( !geometry.sun_xy || geometry.sun_xy.length != 2 )
      throw new Error( "Geometry must contain sun_xy: [x, y]." );
   if ( !( geometry.sun_radius_px > 0 ) )
      throw new Error( "sun_radius_px must be greater than zero." );
   if ( (geometry.moon_xy == null) != (geometry.moon_radius_px == null) )
      throw new Error( "Set both moon_xy and moon_radius_px, or leave both empty." );
   if ( geometry.moon_radius_px != null && !( geometry.moon_radius_px > 0 ) )
      throw new Error( "moon_radius_px must be greater than zero." );
   return geometry;
}

function aelBridgeUniqueOutput( root, mode )
{
   if ( !root || root.trim().length == 0 )
      throw new Error( "Select an output folder." );
   if ( !File.directoryExists( root ) )
      File.createDirectory( root, true );
   let base = root + "/ael_" + mode + "_" + aelBridgeTimestamp();
   let path = base;
   let suffix = 1;
   while ( File.directoryExists( path ) || File.exists( path ) )
      path = base + "_" + String( ++suffix );
   File.createDirectory( path, false );
   return path;
}

function aelBridgeOpenResults( files, mode, openedWindows )
{
   let stamp = aelBridgeTimestamp();
   for ( let key in files )
   {
      let path = files[key];
      let lower = path.toLowerCase();
      if ( !lower.endsWith( ".tif" ) && !lower.endsWith( ".tiff" ) && !lower.endsWith( ".png" ) )
         continue;
      if ( !File.exists( path ) )
         throw new Error( "AEL did not create the declared result: " + path );
      let windows = ImageWindow.open( path, aelBridgeId( "AEL_" + mode + "_" + key + "_" + stamp ) );
      if ( windows == null || windows.length == 0 )
         throw new Error( "PixInsight could not open AEL result: " + path );
      for ( let i = 0; i < windows.length; ++i )
      {
         openedWindows.push( windows[i] );
         windows[i].show();
      }
   }
}

function aelBridgeCleanup( directory, files )
{
   for ( let i = 0; i < files.length; ++i )
      if ( File.exists( files[i] ) )
         try { File.remove( files[i] ); } catch ( error ) { Console.warningln( "Could not remove temporary file: " + files[i] ); }
   if ( File.directoryExists( directory ) )
      try { File.removeDirectory( directory ); } catch ( error ) { Console.warningln( "Could not remove temporary directory: " + directory ); }
}

function aelBridgeRunOnView( parameters )
{
   let view = parameters.view;
   let mode = parameters.mode;
   if ( mode != "structure" && mode != "polar" )
      throw new Error( "Mode must be 'structure' or 'polar'." );
   aelBridgeValidateGeometry( parameters.geometry, view );

   let runtime = parameters.runtime || aelBridgeCandidates( parameters.pythonPath, parameters.aelRoot );
   if ( !runtime.ok )
      throw new Error( runtime.message || "Python preflight failed." );
   Settings.write( AEL_BRIDGE_SETTINGS_KEY + "pythonPath", DataType.UTF8String, runtime.python );

   // A view that the user has processed since opening it is theirs, and it is exported. One that is still its file must
   // hold what the file holds, and PixInsight does not always read a floating-point TIFF faithfully: a file with values
   // outside 0-1 is rescaled to 0-1 (the zero and the scale are lost), and one whose last sample is NaN (no data in the
   // bottom-right corner, which a registered stack often has) is read as a completely black image. AEL does not give the
   // result it gives on the file on either of those, so then AEL reads the file itself, as `python -m ael` does.
   let sourcePath = view.window.filePath;
   let sourceRange = view.window.isModified ? null : aelBridgeSourceRange( runtime, parameters.aelRoot, view );
   let scan = aelBridgeScanView( view );
   let fileReasons = [];
   if ( sourceRange )
   {
      let shape = aelBridgeFileShapeDifference( sourceRange, view );
      if ( shape.length > 0 )
         throw new Error( "The file this image was opened from does not have the size of the image (" + shape
                          + "), so nothing was run. If you have processed the image since opening it, this check does not apply." );
      if ( sourceRange.outside_unit_range )
         fileReasons.push( "PixInsight rescaled the file when it opened it: the file holds values from " + sourceRange.minimum
                           + " to " + sourceRange.maximum + " and PixInsight maps that range to 0-1" );
      else
         fileReasons = aelBridgeFileDifferences( sourceRange, scan );
      if ( fileReasons.length > 0 && sourceRange.last_sample_is_nan )
         fileReasons.push( "the last sample of the file is NaN, and PixInsight reads a floating-point TIFF whose last sample is NaN "
                           + "as a black image" );
   }
   let onFile = fileReasons.length > 0;

   let tempDir = File.systemTempDirectory + "/pixinsight-ael-" + aelBridgeTimestamp();
   File.createDirectory( tempDir, false );
   let geometryPath = tempDir + "/geometry.json";
   let temporaryFiles = [ geometryPath ];            // never the file the image was opened from
   let openedWindows = [];
   let outputDirectory = "";

   try
   {
      let inputPath, exported = null, inspected, nonFinite = 0;
      if ( onFile )
      {
         inputPath = sourcePath;
         nonFinite = sourceRange.nonfinite_samples;
         Console.writeln( "AEL bridge: the view is not the file it was opened from (" + fileReasons.join( "; " ) + "). "
                          + "AEL reads the file itself: " + sourcePath );
         inspected = { dtype: sourceRange.dtype, shape: sourceRange.shape, planar: 1, icc_bytes: 0, icc_repaired: false,
                       nonfinite_restored: 0, nonfinite_written_as: [], sha256: sourceRange.sha256, bytes: sourceRange.bytes };
      }
      else
      {
         inputPath = tempDir + "/input_float32.tif";
         temporaryFiles.push( inputPath, inputPath + ".icc" );
         exported = aelBridgeExportFloat32( view, inputPath );
         let nonFinitePath = tempDir + "/nonfinite_positions.u32";
         temporaryFiles.push( nonFinitePath );
         nonFinite = scan.nonFinite;
         aelBridgeWriteNonFinite( scan, nonFinitePath );
         if ( nonFinite > 0 )
            Console.writeln( "AEL bridge: " + nonFinite + " samples hold no data (NaN); PixInsight writes them to a TIFF as 1.0, "
                             + "so they are put back as NaN for AEL, as in the file." );
         inspected = aelBridgeInspectInput( runtime, parameters.aelRoot, inputPath, view,
                                            exported.sourceICCBytes, exported.iccSidecar,
                                            nonFinite > 0 ? nonFinitePath : "" );
      }
      File.writeTextFile( geometryPath, JSON.stringify( parameters.geometry, null, 1 ) );
      outputDirectory = parameters.outputDirectoryExact || aelBridgeUniqueOutput( parameters.outputDirectory, mode );
      if ( parameters.outputDirectoryExact && !File.directoryExists( outputDirectory ) )
         File.createDirectory( outputDirectory, true );

      let arguments = [ "-m", "ael", mode, "--input", inputPath, "--geometry", geometryPath, "--out", outputDirectory ];
      if ( mode == "structure" )
      {
         arguments.push( "--name", "structure" );
         if ( parameters.validMask && parameters.validMask.trim().length > 0 )
            arguments.push( "--valid", parameters.validMask.trim() );
      }
      else
         arguments.push( "--rmax", String( parameters.rmax || 4.0 ) );

      Console.writeln( "AEL bridge: " + mode + " with " + runtime.ael_version + " (" + runtime.ael_file + ")" );
      let run = aelBridgeRun( runtime.python, arguments,
                              parameters.aelRoot && parameters.aelRoot.length ? parameters.aelRoot : tempDir,
                              aelBridgeEnvironment( parameters.aelRoot ), parameters.timeoutMs || 600000 );
      if ( run.timedOut )
         throw new Error( "AEL exceeded the execution time limit and was stopped." );
      if ( !run.ok )
         throw new Error( "AEL failed with exit code " + run.exitCode + ".\n" + run.stderr + "\n" + run.stdout );
      let result = aelBridgeParseJson( run.stdout, "AEL " + mode );
      if ( mode == "structure" && ( !result.gate || !result.gate.passed ) )
         throw new Error( "AEL structure gate failed; no result will be delivered." );
      if ( !result.files )
         throw new Error( "AEL returned no result files." );

      File.copyFile( outputDirectory + "/input_geometry.json", geometryPath );
      let receiptPath = outputDirectory + "/AEL_BRIDGE_RECEIPT.json";
      let bridgeReceipt = {
         product: "PixInsight AEL bridge: " + mode,
         created: new Date().toISOString(),
         command: [ runtime.python ].concat( arguments ),
         runtime: { python: runtime.python, python_version: runtime.version,
                    ael_version: runtime.ael_version, ael_file: runtime.ael_file },
         source: { view_id: view.id, width: view.image.width, height: view.image.height,
                   channels: view.image.numberOfChannels,
                   icc_bytes: exported ? exported.sourceICCBytes : 0,
                   icc_origin: exported ? exported.iccOrigin : "not used: AEL read the file itself",
                   non_finite_samples: nonFinite,
                   file_range: sourceRange ? { minimum: sourceRange.minimum, maximum: sourceRange.maximum } : null,
                   ael_input: onFile ? "the file the image was opened from" : "the view, exported to a temporary TIFF",
                   file_path: onFile ? sourcePath : null, file_reasons: fileReasons },
         temporary_input: onFile ? null : { format: "TIFF", dtype: inspected.dtype, shape: inspected.shape,
                            planar: inspected.planar, icc_bytes: inspected.icc_bytes,
                            icc_repaired: inspected.icc_repaired == true,
                            nonfinite_restored: inspected.nonfinite_restored || 0,
                            nonfinite_written_by_pixinsight_as: inspected.nonfinite_written_as || [],
                            sha256: inspected.sha256, bytes: inspected.bytes },
         input_file: onFile ? { path: sourcePath, dtype: inspected.dtype, shape: inspected.shape,
                                sha256: inspected.sha256, bytes: inspected.bytes } : null,
         geometry: "input_geometry.json",
         ael_receipt: result.receipt || null,
         gate: result.gate || { passed: true, reason: "AEL polar completed; declared image files checked by the bridge" },
         files: result.files,
         credit: AEL_BRIDGE_CREDIT
      };
      File.writeTextFile( receiptPath, JSON.stringify( bridgeReceipt, null, 1 ) );
      aelBridgeOpenResults( result.files, mode, openedWindows );

      Console.writeln( "AEL bridge receipt: " + receiptPath );
      Console.writeln( File.readTextFile( receiptPath ) );
      if ( result.receipt && File.exists( result.receipt ) )
      {
         Console.writeln( "AEL receipt: " + result.receipt );
         Console.writeln( File.readTextFile( result.receipt ) );
      }
      return { outputDirectory: outputDirectory, receipt: receiptPath, result: result,
               runtime: runtime, input: inspected, windows: openedWindows };
   }
   catch ( error )
   {
      for ( let i = 0; i < openedWindows.length; ++i )
         openedWindows[i].forceClose();
      throw error;
   }
   finally
   {
      aelBridgeCleanup( tempDir, temporaryFiles );
   }
}

#endif // __AEL_BRIDGE_CORE_jsh
