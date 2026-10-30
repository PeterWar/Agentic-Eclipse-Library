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

var AELWorkflowDialog = class extends Dialog
{
   constructor()
   {
      super();
      this.windowTitle = "AEL Linear Master and Filter Layers";
      this.userResizable = true;
      this.scaledMinWidth = 620;
      this.frames = [];
      // Not shown: the Python is found by the connector, AEL is the one that comes with it, and the PixelMath composite
      // is always built. A script or a test may set them before Run.
      this.pythonPath = Settings.read( AEL_BRIDGE_SETTINGS_KEY + "pythonPath", DataType.UTF8String ) || "";
      this.aelRoot = aelBridgeInitialRoot();
      this.buildComposite = true;
      this.sizer = new VerticalSizer;
      this.sizer.margin = 10;
      this.sizer.spacing = 7;

      let intro = new Label( this );
      intro.wordWrapping = true;
      intro.useRichText = true;
      intro.text = "<b>AEL filter layers</b><br>AEL's filter layers and an adjustable PixelMath composite, made from a "
                   + "linear stack (TIFF, FITS or AEL's linear.npy). AEL finds the Moon on the image by itself.";
      this.sizer.add( intro );

      let notice = new Label( this );
      notice.wordWrapping = true;
      notice.useRichText = true;
      notice.text = "<b>Experimental.</b> The filter layers are validated with synthetic data. "
                    + "The linear master registers every frame on the Sun, and on real eclipse frames that registration "
                    + "is not valid yet: it lands 0.07-2.2 px from the reference registration. Do not use it on real frames.";
      this.sizer.add( notice );

      let modeSizer = new HorizontalSizer;
      modeSizer.spacing = 6;
      let modeLabel = new Label( this );
      modeLabel.text = "Operation:";
      this.modeList = new ComboBox( this );
      this.modeList.addItem( "Filter layers from a linear stack" );
      this.modeList.addItem( "Linear master from totality frames (experimental)" );
      this.modeList.currentItem = 0;
      modeSizer.add( modeLabel );
      modeSizer.add( this.modeList );
      modeSizer.addStretch();
      this.sizer.add( modeSizer );

      let filesLabel = new Label( this );
      this.sizer.add( filesLabel );
      this.filesText = new TextBox( this );
      this.filesText.readOnly = true;
      this.filesText.setScaledFixedHeight( 64 );
      this.sizer.add( this.filesText );
      let fileButtons = new HorizontalSizer;
      fileButtons.spacing = 6;
      let addButton = new PushButton( this );
      addButton.text = "Add files…";
      addButton.onClick = function()
      {
         let chooser = new OpenFileDialog;
         chooser.caption = this.dialog.modeList.currentItem == 0 ? "Select a linear stack" : "Select totality frames";
         chooser.multipleSelections = this.dialog.modeList.currentItem == 1;
         if ( chooser.execute() )
         {
            for ( let i = 0; i < chooser.fileNames.length; ++i )
               if ( this.dialog.frames.indexOf( chooser.fileNames[i] ) < 0 )
                  this.dialog.frames.push( chooser.fileNames[i] );
            this.dialog.updateFiles();
         }
      };
      let clearButton = new PushButton( this );
      clearButton.text = "Clear";
      clearButton.onClick = function() { this.dialog.frames = []; this.dialog.updateFiles(); };
      fileButtons.add( addButton );
      fileButtons.add( clearButton );
      fileButtons.addStretch();
      this.sizer.add( fileButtons );

      let rows = [];
      function pathRow( parent, label, directory )
      {
         let row = new HorizontalSizer;
         row.spacing = 6;
         let caption = new Label( parent );
         caption.text = label;
         caption.setScaledFixedWidth( 150 );
         let edit = new Edit( parent );
         let button = new ToolButton( parent );
         button.icon = parent.scaledResource( directory ? ":/icons/select-folder.png" : ":/icons/select-file.png" );
         button.setScaledFixedSize( 24, 24 );
         button.onClick = function()
         {
            if ( directory )
            {
               let chooser = new GetDirectoryDialog;
               chooser.caption = label;
               if ( edit.text.length > 0 )
                  chooser.initialPath = edit.text;
               if ( chooser.execute() )
                  edit.text = chooser.directory;
            }
            else
            {
               let chooser = new OpenFileDialog;
               chooser.caption = label;
               if ( chooser.execute() )
                  edit.text = chooser.fileName;
            }
         };
         row.add( caption );
         row.add( edit, 100 );
         row.add( button );
         parent.sizer.add( row );
         rows.push( [ caption, edit, button ] );
         return edit;
      }
      // Dark and flat belong to the linear master only.
      this.darkEdit = pathRow( this, "Master dark (optional):", false );
      this.flatEdit = pathRow( this, "Master flat (optional):", false );
      let calibrationRows = rows.slice();
      this.outputEdit = pathRow( this, "Output folder:", true );
      let saved = Settings.read( AEL_BRIDGE_SETTINGS_KEY + "workflowOutput", DataType.UTF8String );
      if ( saved ) this.outputEdit.text = saved;

      this.allFiltersCheck = new CheckBox( this );
      this.allFiltersCheck.text = "All 16 filters (otherwise AEL's three default layers: NRGF, edge-aware WOW and ACHF 04)";
      this.allFiltersCheck.checked = true;
      this.sizer.add( this.allFiltersCheck );

      let buttons = new HorizontalSizer;
      buttons.spacing = 8;
      let runButton = new PushButton( this );
      this.runButton = runButton;
      runButton.text = "Run workflow";
      runButton.defaultButton = true;
      let cancelButton = new PushButton( this );
      cancelButton.text = "Cancel";
      cancelButton.onClick = function() { this.dialog.cancel(); };
      buttons.addStretch();
      buttons.add( runButton );
      buttons.add( cancelButton );
      this.sizer.add( buttons );

      this.updateFiles = function()
      {
         this.filesText.text = this.frames.join( "\n" );
      };
      this.updateOperation = function()
      {
         let master = this.modeList.currentItem == 1;
         filesLabel.text = master ? "Totality frames (RAW, TIFF or FITS; one camera and one ISO):"
                                  : "Linear stack (one file):";
         for ( let i = 0; i < calibrationRows.length; ++i )
            for ( let j = 0; j < calibrationRows[i].length; ++j )
               calibrationRows[i][j].visible = master;
         notice.visible = master;
      };
      this.modeList.onItemSelected = function() { this.dialog.updateOperation(); this.dialog.adjustToContents(); };

      runButton.onClick = function()
      {
         let configPath = "";
         try
         {
            let master = this.dialog.modeList.currentItem == 1;
            if ( this.dialog.frames.length == 0 )
               throw new Error( master ? "Add at least one totality frame." : "Add a linear stack." );
            if ( !master && this.dialog.frames.length > 1 )
               throw new Error( "Add one linear stack only." );
            if ( !this.dialog.outputEdit.text.trim() )
               throw new Error( "Select an output folder." );
            let outputRoot = this.dialog.outputEdit.text.trim();
            if ( !File.directoryExists( outputRoot ) )
               File.createDirectory( outputRoot, true );
            let base = outputRoot + "/ael_" + (master ? "master" : "filters") + "_" + aelBridgeTimestamp();
            let output = base;
            let suffix = 1;
            while ( File.exists( output ) || File.directoryExists( output ) )
               output = base + "_" + String( ++suffix );
            // "defaults" is read by the helper from ael.filterbank.DEFAULTS; without it the helper would make all 16.
            let filterOptions = { filters: this.dialog.allFiltersCheck.checked ? "all" : "defaults" };
            // No geometry and no camera profile: AEL measures them and the receipt says what was measured and assumed.
            let config = master ? {
               frames: this.dialog.frames, reference: 0, camera: "auto", geometry: "auto",
               out: output, run_filters: true, filter_options: filterOptions
            } : {
               input: this.dialog.frames[0], out: output, filters: filterOptions.filters
            };
            if ( master && this.dialog.darkEdit.text.trim() ) config.dark = this.dialog.darkEdit.text.trim();
            if ( master && this.dialog.flatEdit.text.trim() ) config.flat = this.dialog.flatEdit.text.trim();
            configPath = File.systemTempDirectory + "/ael-workflow-" + aelBridgeTimestamp() + ".json";
            File.writeTextFile( configPath, JSON.stringify( config, null, 1 ) );
            let runtime = aelBridgeCandidates( this.dialog.pythonPath, this.dialog.aelRoot );
            Settings.write( AEL_BRIDGE_SETTINGS_KEY + "workflowOutput", DataType.UTF8String, outputRoot );
            this.dialog.ok();
            aelWorkflowRunAndOpen( master ? "master" : "filters", configPath, runtime, this.dialog.aelRoot,
                                   this.dialog.buildComposite );
         }
         catch ( error )
         {
            Console.criticalln( "AEL workflow: " + error );
            new MessageBox( String( error ), "AEL workflow", StdIcon.Error, StdButton.Ok ).execute();
         }
         finally
         {
            if ( configPath && File.exists( configPath ) )
               File.remove( configPath );
         }
      };
      this.updateOperation();
      this.adjustToContents();
   }
};
