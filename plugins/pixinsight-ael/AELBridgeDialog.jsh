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
// what to make, from which RAW photos or which open image, and where to save it.
var AEL_OPERATIONS = [ "Stacked image from RAW photos", "Structure image", "Unrolled view of the corona",
                       "Filter layers and PixelMath composite" ];
// The RAW files the stacked image is made from, the same as in the Photoshop connector.
var AEL_RAW_PATTERNS = [ "*.cr2", "*.cr3", "*.nef", "*.arw", "*.dng", "*.raf", "*.orf", "*.rw2" ];

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
      this.raw = [];
      this.calibration = [];
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
      intro.text = "<b>Agentic Eclipse Library</b><br>Choose the RAW photos of the totality: AEL stacks them into one "
                   + "image with its filter layers and opens it here. Or make a structure image, an unrolled view or the "
                   + "filter layers of an open image. AEL finds the Moon and the Sun by itself; your files are not changed.";
      this.sizer.add( intro );

      let dialog = this;
      // every caption as wide as the widest, so that the fields line up
      let captionWidth = this.logicalPixelsToPhysical( 8 ) + Math.max.apply( null,
         [ "Make:", "Image:", "Totality RAW photos:", "Darks and flats (optional):", "Output folder:" ].map(
            function( text ) { return dialog.font.width( text ); } ) );
      function captioned( text, parent )
      {
         let label = new Label( parent || dialog );
         label.text = text;
         label.textAlignment = TextAlign_Right | TextAlign_VertCenter;
         label.setFixedWidth( captionWidth );
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

      // From RAW photos: the totality and, if there are any, darks and flats mixed (AEL tells them apart). Each list takes
      // several files at once, in one container that hides as a whole; a file that is not RAW is not added.
      let rawRows = [];
      function isRaw( path )
      {
         return AEL_RAW_PATTERNS.indexOf( "*" + File.extractExtension( path ).toLowerCase() ) >= 0;
      }
      function fileList( text, key, height, caption, tip )
      {
         let box = new Control( dialog );
         box.sizer = new HorizontalSizer;
         box.sizer.spacing = 6;
         box.toolTip = tip;
         let label = captioned( text, box );
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
            chooser.filters = [ [ "RAW photos" ].concat( AEL_RAW_PATTERNS,
                                  AEL_RAW_PATTERNS.map( function( pattern ) { return pattern.toUpperCase(); } ) ) ];
            if ( chooser.execute() )
            {
               for ( let i = 0; i < chooser.fileNames.length; ++i )
               {
                  let path = chooser.fileNames[i];
                  if ( !isRaw( path ) )
                     Console.warningln( "Not a RAW photo, not added: " + path );
                  else if ( dialog[key].indexOf( path ) < 0 )
                     dialog[key].push( path );
               }
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
         rawRows.push( box );
         return { list: list, add: add };
      }
      let raw = fileList( "Totality RAW photos:", "raw", 80, "RAW photos of the totality (select them all)",
                          "The RAW photos of the totality, of one camera. AEL leaves out what it cannot stack (another "
                          + "camera or ISO, the diamond ring, another pointing of the mount) and says why." );
      let calibration = fileList( "Darks and flats (optional):", "calibration", 60,
                                  "Dark and flat frames of the same camera",
                                  "Darks and flats of the same camera, mixed: AEL tells them apart, makes a master dark for "
                                  + "each exposure of the photos and a master flat." );
      this.rawText = raw.list;
      this.addRawButton = raw.add;
      this.calibrationText = calibration.list;
      this.addCalibrationButton = calibration.add;

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

      this.allFiltersCheck = new CheckBox( this );
      this.allFiltersCheck.text = "All 16 filters (otherwise AEL's three default layers: NRGF, edge-aware WOW and ACHF 04)";
      this.allFiltersCheck.checked = true;
      let filtersSizer = new HorizontalSizer;
      filtersSizer.addSpacing( captionWidth + this.logicalPixelsToPhysical( 6 ) );
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
         this.rawText.text = names( this.raw );
         this.calibrationText.text = names( this.calibration );
      };
      // Each operation shows only what it needs.
      this.updateOperation = function()
      {
         let mode = this.modeList.currentItem;
         for ( let i = 0; i < rawRows.length; ++i )
            rawRows[i].visible = mode == 0;
         rmaxLabel.visible = mode == 2;
         this.rmaxEdit.visible = mode == 2;
         imageLabel.visible = mode >= 1;
         this.imageList.visible = mode >= 1;
         this.allFiltersCheck.visible = mode == 3;
      };
      this.modeList.onItemSelected = function() { this.dialog.updateOperation(); this.dialog.adjustToContents(); };

      runButton.onClick = function()
      {
         let d = this.dialog;
         try
         {
            let mode = d.modeList.currentItem;
            let outputRoot = d.outputEdit.text.trim();
            if ( !outputRoot )
               throw new Error( "Choose an output folder." );
            if ( mode == 0 && d.raw.length == 0 )
               throw new Error( "Choose the RAW photos of the totality first." );
            if ( mode >= 1 && !d.targetView )
               throw new Error( "Open an image and select it." );
            Settings.write( AEL_BRIDGE_SETTINGS_KEY + "outputDirectory", DataType.UTF8String, outputRoot );
            d.ok();
            if ( mode == 0 )
               aelWorkflowRaw( d.raw, d.calibration, outputRoot, d.pythonPath, d.aelRoot, d.buildComposite );
            else if ( mode <= 2 )
               aelBridgeRunOnView( { view: d.targetView, mode: mode == 1 ? "structure" : "polar", geometry: null,
                                     outputDirectory: outputRoot, pythonPath: d.pythonPath, aelRoot: d.aelRoot,
                                     rmax: parseFloat( d.rmaxEdit.text ) } );
            else
               aelWorkflowFiltersFromView( d.targetView, outputRoot, d.allFiltersCheck.checked ? "all" : "defaults",
                                           d.pythonPath, d.aelRoot, d.buildComposite );
         }
         catch ( error )
         {
            Console.criticalln( "Agentic Eclipse Library: " + error );
            new MessageBox( String( error ), "Agentic Eclipse Library", StdIcon.Error, StdButton.Ok ).execute();
         }
      };

      this.updateOperation();
      this.adjustToContents();
   }
};
