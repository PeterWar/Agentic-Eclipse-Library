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

#engine v8
#feature-id AELBridge : Utilities > Agentic Eclipse Library
#feature-info Structure images, unrolled views and filter layers of the corona from an open image, or a linear master from totality frames (experimental), made by the Agentic Eclipse Library.

#include "AELWorkflowCore.jsh"
#include "AELBridgeDialog.jsh"

CoreApplication.ensureMinimumVersion( 1, 9, 4 );

function main()
{
   try
   {
      let dialog = new AELBridgeDialog;
      dialog.execute();
   }
   catch ( error )
   {
      Console.criticalln( "Agentic Eclipse Library: " + error );
      new MessageBox( String( error ), "Agentic Eclipse Library", StdIcon.Error, StdButton.Ok ).execute();
   }
}
main();
