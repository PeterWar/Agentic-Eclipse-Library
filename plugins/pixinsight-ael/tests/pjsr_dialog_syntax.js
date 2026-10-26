/* MIT License — Copyright (c) 2026 Pere Guerra Serra.
 * Processed with Agentic Eclipse Library by Pere Guerra —
 * https://github.com/PeterWar/Agentic-Eclipse-Library
 * Parser/load check with an on-disk diagnostic. */
#engine v8
#include "../AELBridgeCore.jsh"
var testDirectory = File.extractDrive( #__FILE__ ) + File.extractDirectory( #__FILE__ );
try
{
   let source = File.readTextFile( testDirectory + "/../AELBridgeDialog.jsh" );
   source = source.replace( /^\s*#.*$/gm, "" );
   eval( source );
   File.writeTextFile( File.systemTempDirectory + "/ael-dialog-syntax-ok.txt", "loaded" );
}
catch ( error )
{
   File.writeTextFile( File.systemTempDirectory + "/ael-dialog-syntax-error.txt", String( error ) );
}
