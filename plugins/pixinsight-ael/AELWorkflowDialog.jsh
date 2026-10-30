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
      this.scaledMinWidth = 760;
      this.frames = [];
      this.sizer = new VerticalSizer;
      this.sizer.margin = 10;
      this.sizer.spacing = 7;

      let intro = new Label( this );
      intro.wordWrapping = true;
      intro.useRichText = true;
      intro.text = "<b>Automated AEL workflow</b><br>One camera and one ISO. Metadata, registration on the Sun, recipes, "
                   + "filter TIFFs and PixelMath expressions are generated automatically. "
                   + "Calibration and reference geometry are required, never guessed.";
      this.sizer.add( intro );

      let notice = new Label( this );
      notice.wordWrapping = true;
      notice.useRichText = true;
      notice.text = "<b>Experimental.</b> The <i>filter layers from linear.npy</i> operation is validated with synthetic data. "
                    + "The <i>linear master</i> registers every frame on the Sun, and on real eclipse frames that registration "
                    + "is not valid yet: it lands 0.07-2.2 px from the reference registration. Do not use it on real frames.";
      this.sizer.add( notice );

      let modeSizer = new HorizontalSizer;
      modeSizer.spacing = 6;
      let modeLabel = new Label( this );
      modeLabel.text = "Operation:";
      this.modeList = new ComboBox( this );
      this.modeList.addItem( "Linear master + all filter layers" );
      this.modeList.addItem( "Filter layers from linear.npy" );
      this.modeList.currentItem = 0;
      modeSizer.add( modeLabel );
      modeSizer.add( this.modeList );
      modeSizer.addStretch();
      this.sizer.add( modeSizer );

      let filesLabel = new Label( this );
      filesLabel.text = "Totality frames (or one linear.npy for filter-only mode):";
      this.sizer.add( filesLabel );
      this.filesText = new TextBox( this );
      this.filesText.readOnly = true;
      this.filesText.setScaledFixedHeight( 74 );
      this.sizer.add( this.filesText );
      let fileButtons = new HorizontalSizer;
      fileButtons.spacing = 6;
      let addButton = new PushButton( this );
      addButton.text = "Add files…";
      addButton.onClick = function()
      {
         let chooser = new OpenFileDialog;
         chooser.caption = "Select totality frames or linear.npy";
         chooser.multipleSelections = true;
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

      function pathRow( parent, label, directory )
      {
         let row = new HorizontalSizer;
         row.spacing = 6;
         let caption = new Label( parent );
         caption.text = label;
         caption.setScaledFixedWidth( 160 );
         let edit = new Edit( parent );
         let button = new ToolButton( parent );
         button.icon = parent.scaledResource( ":/icons/select-file.png" );
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
         return edit;
      }

      this.geometryEdit = pathRow( this, "Reference geometry JSON:", false );
      this.cameraEdit = pathRow( this, "Camera profile JSON:", false );
      this.darkEdit = pathRow( this, "Master dark (optional):", false );
      this.flatEdit = pathRow( this, "Master flat (optional):", false );
      this.outputEdit = pathRow( this, "Output folder:", true );
      this.pythonEdit = pathRow( this, "Python executable:", false );
      this.aelRootEdit = pathRow( this, "AEL folder (optional):", true );

      let saved = Settings.read( AEL_BRIDGE_SETTINGS_KEY + "pythonPath", DataType.UTF8String );
      if ( saved ) this.pythonEdit.text = saved;
      this.aelRootEdit.text = aelBridgeInitialRoot();
      saved = Settings.read( AEL_BRIDGE_SETTINGS_KEY + "workflowOutput", DataType.UTF8String );
      if ( saved ) this.outputEdit.text = saved;
      saved = Settings.read( AEL_BRIDGE_SETTINGS_KEY + "workflowGeometry", DataType.UTF8String );
      if ( saved ) this.geometryEdit.text = saved;
      saved = Settings.read( AEL_BRIDGE_SETTINGS_KEY + "workflowCamera", DataType.UTF8String );
      if ( saved ) this.cameraEdit.text = saved;

      this.allFiltersCheck = new CheckBox( this );
      this.allFiltersCheck.text = "Generate all 16 filters (otherwise only AEL's default layers: NRGF, edge-aware WOW and ACHF 04)";
      this.allFiltersCheck.checked = true;
      this.sizer.add( this.allFiltersCheck );
      this.compositeCheck = new CheckBox( this );
      this.compositeCheck.text = "Build an adjustable PixelMath composite on a duplicate of the display base";
      this.compositeCheck.checked = true;
      this.sizer.add( this.compositeCheck );

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

      runButton.onClick = function()
      {
         let configPath = "";
         try
         {
            let master = this.dialog.modeList.currentItem == 0;
            if ( this.dialog.frames.length == 0 )
               throw new Error( master ? "Add at least one totality frame." : "Select linear.npy." );
            if ( !this.dialog.outputEdit.text.trim() )
               throw new Error( "Select an output folder." );
            if ( master && !this.dialog.geometryEdit.text.trim() )
               throw new Error( "Reference geometry is required; it is not guessed." );
            if ( master && !this.dialog.cameraEdit.text.trim() )
               throw new Error( "Camera profile is required; black and white levels are not guessed." );
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
            let config = master ? {
               frames: this.dialog.frames, reference: 0,
               camera: this.dialog.cameraEdit.text.trim(),
               geometry: this.dialog.geometryEdit.text.trim(),
               out: output, run_filters: true, filter_options: filterOptions
            } : {
               input: this.dialog.frames[0], out: output,
               filters: filterOptions.filters
            };
            if ( master && this.dialog.darkEdit.text.trim() ) config.dark = this.dialog.darkEdit.text.trim();
            if ( master && this.dialog.flatEdit.text.trim() ) config.flat = this.dialog.flatEdit.text.trim();
            configPath = File.systemTempDirectory + "/ael-workflow-" + aelBridgeTimestamp() + ".json";
            File.writeTextFile( configPath, JSON.stringify( config, null, 1 ) );
            let runtime = aelBridgeCandidates( this.dialog.pythonEdit.text.trim(), this.dialog.aelRootEdit.text.trim() );
            Settings.write( AEL_BRIDGE_SETTINGS_KEY + "workflowOutput", DataType.UTF8String, outputRoot );
            Settings.write( AEL_BRIDGE_SETTINGS_KEY + "workflowGeometry", DataType.UTF8String, this.dialog.geometryEdit.text.trim() );
            Settings.write( AEL_BRIDGE_SETTINGS_KEY + "workflowCamera", DataType.UTF8String, this.dialog.cameraEdit.text.trim() );
            Settings.write( AEL_BRIDGE_SETTINGS_KEY + "aelRoot", DataType.UTF8String, this.dialog.aelRootEdit.text.trim() );
            this.dialog.ok();
            aelWorkflowRunAndOpen( master ? "master" : "filters", configPath, runtime,
                                   this.dialog.aelRootEdit.text.trim(), this.dialog.compositeCheck.checked );
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
      this.adjustToContents();
   }
};
