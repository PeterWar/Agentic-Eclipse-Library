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

#include <pjsr/TextAlign.jsh>

// The one dialog of the connector (Script > Utilities > Agentic Eclipse Library). It asks only for what a person knows:
// what to make, from which open image or which frames, and where to save it.
var AEL_OPERATIONS = [ "Structure image", "Unrolled view of the corona", "Filter layers and PixelMath composite",
                       "Linear master from frames (experimental)" ];

var AELBridgeDialog = class extends Dialog
{
   constructor()
   {
      super();
      this.windowTitle = "Agentic Eclipse Library";
      this.userResizable = true;
      this.scaledMinWidth = 620;

      let active = ImageWindow.activeWindow;
      this.targetView = active.isNull ? undefined : active.mainView;
      this.frames = [];
      // Not shown: the Python is found by the connector (the one that worked last is tried first), AEL is the one that
      // comes with it, and the PixelMath composite is always built. A script or a test may set them before Run.
      this.pythonPath = Settings.read( AEL_BRIDGE_SETTINGS_KEY + "pythonPath", DataType.UTF8String ) || "";
      this.aelRoot = aelBridgeInitialRoot();
      this.buildComposite = true;

      this.sizer = new VerticalSizer;
      this.sizer.margin = 10;
      this.sizer.spacing = 8;
      let intro = new Label( this );
      intro.wordWrapping = true;
      intro.useRichText = true;
      intro.text = "<b>Agentic Eclipse Library</b><br>Structure images, unrolled views and filter layers of the corona from "
                   + "an open image, or a linear master from totality frames. AEL finds the Moon by itself; your images are "
                   + "not changed, and the results open in new windows, with one that shows the circle it found.";
      this.sizer.add( intro );

      let dialog = this;
      function captioned( text )
      {
         let label = new Label( dialog );
         label.text = text;
         label.textAlignment = TextAlign_Right | TextAlign_VertCenter;
         label.setScaledFixedWidth( 110 );
         return label;
      }
      function browseButton( onClick )
      {
         let button = new PushButton( dialog );
         button.text = "Browse…";
         button.onClick = onClick;
         return button;
      }

      // What to make
      let modeSizer = new HorizontalSizer;
      modeSizer.spacing = 6;
      this.modeList = new ComboBox( this );
      for ( let i = 0; i < AEL_OPERATIONS.length; ++i )
         this.modeList.addItem( AEL_OPERATIONS[i] );
      let rmaxLabel = new Label( this );
      rmaxLabel.text = "Radius (solar radii):";
      this.rmaxEdit = new Edit( this );
      this.rmaxEdit.text = "4.0";
      this.rmaxEdit.setScaledFixedWidth( 64 );
      modeSizer.add( captioned( "Make:" ) );
      modeSizer.add( this.modeList );
      modeSizer.addStretch();
      modeSizer.add( rmaxLabel );
      modeSizer.add( this.rmaxEdit );
      this.sizer.add( modeSizer );

      // From an open image (structure, unrolled view, filter layers)
      let imageSizer = new HorizontalSizer;
      imageSizer.spacing = 6;
      let imageLabel = captioned( "Image:" );
      this.imageList = new ViewList( this );
      this.imageList.getMainViews();
      if ( this.targetView )
         this.imageList.currentView = this.targetView;
      this.imageList.onViewSelected = function( view )
      {
         this.dialog.targetView = view && !view.isNull ? view : undefined;
      };
      imageSizer.add( imageLabel );
      imageSizer.add( this.imageList, 100 );
      this.sizer.add( imageSizer );

      // From files (linear master): the frames, and the darks and flats if there are any. Each list takes several files
      // at once (RAW, TIFF or FITS; a master dark or flat may also be AEL's NPY), in one container that hides as a whole.
      let masterRows = [];
      let raw = [ "*.cr2", "*.cr3", "*.nef", "*.arw", "*.dng", "*.raf", "*.orf", "*.rw2", "*.tif", "*.tiff", "*.fit",
                  "*.fits", "*.fts" ];
      function fileList( text, key, height, caption, tip, extensions )
      {
         let box = new Control( dialog );
         box.sizer = new HorizontalSizer;
         box.sizer.spacing = 6;
         box.toolTip = tip;
         let label = new Label( box );
         label.text = text;
         label.setScaledFixedWidth( 110 );
         label.textAlignment = TextAlign_Right | TextAlign_Top;
         let list = new TextBox( box );
         list.readOnly = true;
         list.setScaledFixedHeight( height );
         let add = new PushButton( box );
         add.text = "Add files…";
         add.onClick = function()
         {
            let chooser = new OpenFileDialog;
            chooser.caption = caption;
            chooser.multipleSelections = true;
            // the cameras write upper-case names (_MG_9502.CR2): both cases are listed, whatever the file dialog does
            chooser.filters = [ [ "RAW, TIFF and FITS files" ].concat( extensions,
                                  extensions.map( function( pattern ) { return pattern.toUpperCase(); } ) ),
                                [ "All files", "*" ] ];
            if ( chooser.execute() )
            {
               for ( let i = 0; i < chooser.fileNames.length; ++i )
                  if ( dialog[key].indexOf( chooser.fileNames[i] ) < 0 )
                     dialog[key].push( chooser.fileNames[i] );
               dialog.updateFiles();
            }
         };
         let clear = new PushButton( box );
         clear.text = "Clear";
         clear.onClick = function() { dialog[key] = []; dialog.updateFiles(); };
         let buttons = new VerticalSizer;
         buttons.spacing = 6;
         buttons.add( add );
         buttons.add( clear );
         buttons.addStretch();
         box.sizer.add( label );
         box.sizer.add( list, 100 );
         box.sizer.add( buttons );
         dialog.sizer.add( box );
         masterRows.push( box );
         return { list: list, add: add };
      }
      this.darks = [];
      this.flats = [];
      let frames = fileList( "Frames:", "frames", 80, "Totality frames: RAW, TIFF or FITS (one camera and one ISO)",
                             "Totality frames of one camera at one ISO: RAW, TIFF or FITS.", raw );
      let darks = fileList( "Darks (optional):", "darks", 44, "Darks, or one master dark",
                            "Darks taken with the lens covered, at the exposures and ISO of the frames: AEL makes a master "
                            + "dark for each exposure. Or one master dark.", raw.concat( [ "*.npy" ] ) );
      let flats = fileList( "Flats (optional):", "flats", 44, "Flats, or one master flat",
                            "Flats of the same camera and optics: AEL makes the master flat. Or one master flat.",
                            raw.concat( [ "*.npy" ] ) );
      this.filesText = frames.list;
      this.addFilesButton = frames.add;
      this.darksText = darks.list;
      this.addDarksButton = darks.add;
      this.flatsText = flats.list;
      this.addFlatsButton = flats.add;

      this.allFiltersCheck = new CheckBox( this );
      this.allFiltersCheck.text = "All 16 filters (otherwise AEL's three default layers: NRGF, edge-aware WOW and ACHF 04)";
      this.allFiltersCheck.checked = true;
      let filtersSizer = new HorizontalSizer;
      filtersSizer.addSpacing( this.logicalPixelsToPhysical( 116 ) );
      filtersSizer.add( this.allFiltersCheck );
      filtersSizer.addStretch();
      this.sizer.add( filtersSizer );

      // Where to save: the last folder used while it exists, or Downloads
      let outputSizer = new HorizontalSizer;
      outputSizer.spacing = 6;
      this.outputEdit = new Edit( this );
      let saved = Settings.read( AEL_BRIDGE_SETTINGS_KEY + "outputDirectory", DataType.UTF8String );
      this.outputEdit.text = saved && File.directoryExists( saved ) ? saved : File.homeDirectory + "/Downloads";
      this.outputButton = browseButton( function()
      {
         let chooser = new GetDirectoryDialog;
         chooser.caption = "Output folder";
         if ( this.dialog.outputEdit.text.length > 0 && File.directoryExists( this.dialog.outputEdit.text ) )
            chooser.initialPath = this.dialog.outputEdit.text;
         if ( chooser.execute() )
            this.dialog.outputEdit.text = chooser.directory;
      } );
      outputSizer.add( captioned( "Output folder:" ) );
      outputSizer.add( this.outputEdit, 100 );
      outputSizer.add( this.outputButton );
      this.sizer.add( outputSizer );

      let notice = new Label( this );
      notice.wordWrapping = true;
      notice.useRichText = true;
      notice.text = "<b>Experimental.</b> The filter layers are validated with synthetic data. "
                    + "The linear master places the Sun of every frame from its own Moon and its corona; on real frames "
                    + "of 2024 and 2026 they lie within 0.5-0.9 px of the Moon's straight path, but it has not been checked "
                    + "frame by frame against an independent registration.";
      this.sizer.add( notice );

      let buttons = new HorizontalSizer;
      buttons.spacing = 8;
      let runButton = new PushButton( this );
      this.runButton = runButton;
      runButton.text = "Run";
      runButton.defaultButton = true;
      let cancelButton = new PushButton( this );
      cancelButton.text = "Cancel";
      cancelButton.onClick = function() { this.dialog.cancel(); };
      buttons.addStretch();
      buttons.add( runButton );
      buttons.add( cancelButton );
      this.sizer.add( buttons );

      // The lists show each file's name, one per line; the whole path is what AEL is given.
      function names( paths )
      {
         return paths.map( function( path ) { return File.extractNameAndExtension( path ); } ).join( "\n" );
      }
      this.updateFiles = function()
      {
         this.filesText.text = names( this.frames );
         this.darksText.text = names( this.darks );
         this.flatsText.text = names( this.flats );
      };
      // Each operation shows only what it needs.
      this.updateOperation = function()
      {
         let mode = this.modeList.currentItem;
         rmaxLabel.visible = mode == 1;
         this.rmaxEdit.visible = mode == 1;
         imageLabel.visible = mode <= 2;
         this.imageList.visible = mode <= 2;
         for ( let i = 0; i < masterRows.length; ++i )
            masterRows[i].visible = mode == 3;
         this.allFiltersCheck.visible = mode >= 2;
         notice.visible = mode == 3;
      };
      this.modeList.onItemSelected = function() { this.dialog.updateOperation(); this.dialog.adjustToContents(); };

      runButton.onClick = function()
      {
         let d = this.dialog;
         let configPath = "";
         try
         {
            let mode = d.modeList.currentItem;
            let outputRoot = d.outputEdit.text.trim();
            if ( !outputRoot )
               throw new Error( "Choose an output folder." );
            if ( mode <= 2 && !d.targetView )
               throw new Error( "Open an image and select it." );
            if ( mode == 3 && d.frames.length == 0 )
               throw new Error( "Add the totality frames." );
            Settings.write( AEL_BRIDGE_SETTINGS_KEY + "outputDirectory", DataType.UTF8String, outputRoot );
            let filters = d.allFiltersCheck.checked ? "all" : "defaults";
            d.ok();
            if ( mode <= 1 )
               aelBridgeRunOnView( { view: d.targetView, mode: mode == 0 ? "structure" : "polar", geometry: null,
                                     outputDirectory: outputRoot, pythonPath: d.pythonPath, aelRoot: d.aelRoot,
                                     rmax: parseFloat( d.rmaxEdit.text ) } );
            else if ( mode == 2 )
               aelWorkflowFiltersFromView( d.targetView, outputRoot, filters, d.pythonPath, d.aelRoot, d.buildComposite );
            else
            {
               // No geometry and no camera profile: AEL measures them and the receipt says what was measured and assumed.
               // Several darks or flats make their masters (a master dark for each exposure); one file is the master.
               let config = { frames: d.frames, reference: "auto", camera: "auto", geometry: "auto",
                              out: aelWorkflowNewOutput( outputRoot, "master" ), run_filters: true,
                              filter_options: { filters: filters } };
               if ( d.darks.length > 0 ) config.dark = d.darks;
               if ( d.flats.length > 0 ) config.flat = d.flats;
               configPath = File.systemTempDirectory + "/ael-workflow-" + aelBridgeTimestamp() + ".json";
               File.writeTextFile( configPath, JSON.stringify( config, null, 1 ) );
               let runtime = aelBridgeCandidates( d.pythonPath, d.aelRoot );
               aelWorkflowRunAndOpen( "master", configPath, runtime, d.aelRoot, d.buildComposite );
            }
         }
         catch ( error )
         {
            Console.criticalln( "Agentic Eclipse Library: " + error );
            new MessageBox( String( error ), "Agentic Eclipse Library", StdIcon.Error, StdButton.Ok ).execute();
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
