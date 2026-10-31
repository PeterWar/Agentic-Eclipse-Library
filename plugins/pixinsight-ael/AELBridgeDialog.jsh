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
// What each one does, under the list and when the pointer rests on it.
var AEL_OPERATION_HELP = [
   "Stacks the RAW photos of the totality (with their darks and flats, if you add them) into one linear image, then "
   + "makes AEL's filter layers and their PixelMath composite from it.",
   "From an open image: a structure image of the corona, in which the fine filaments show at every radius.",
   "From an open image: the corona unrolled around the Sun, position angle across and radius up, out to the radius "
   + "you set.",
   "From an open image: AEL's filter layers and their PixelMath composite, as for the RAW photos but without stacking."
];
// The RAW files the stacked image is made from, the same as in the Photoshop connector.
var AEL_RAW_PATTERNS = [ "*.cr2", "*.cr3", "*.nef", "*.arw", "*.dng", "*.raf", "*.orf", "*.rw2" ];

// The advanced settings: which of AEL's filters become layers, and how much of each goes into the composite.
var AELFiltersDialog = class extends Dialog
{
   constructor( choice )
   {
      super();
      this.windowTitle = "Advanced settings";
      this.choice = choice;
      this.sizer = new VerticalSizer;
      this.sizer.margin = 10;
      this.sizer.spacing = 6;
      let intro = new Label( this );
      intro.wordWrapping = true;
      intro.text = "Each filter you tick becomes a layer, with its mask. One with an opacity above 0 % also goes into "
                   + "the PixelMath composite, in its blend mode; at 0 % it opens on its own. Rest the pointer on a "
                   + "filter to see what it shows.";
      this.sizer.add( intro );
      this.rows = [];
      let dialog = this;
      for ( let i = 0; i < AEL_FILTERS.length; ++i )
      {
         let filter = AEL_FILTERS[i];
         let row = new HorizontalSizer;
         row.spacing = 6;
         let check = new CheckBox( this );
         check.text = filter.label;
         check.toolTip = filter.about;
         check.checked = choice.filters.indexOf( filter.name ) >= 0;
         check.setScaledMinWidth( 230 );
         let mode = new Label( this );
         mode.text = filter.mode;
         mode.setScaledMinWidth( 60 );
         mode.toolTip = filter.about;
         let opacity = new SpinBox( this );
         opacity.minValue = 0;
         opacity.maxValue = 100;
         opacity.suffix = " %";
         opacity.value = Math.round( 100 * ( check.checked ? ( choice.opacities[filter.name] || 0 ) : filter.opacity ) );
         opacity.toolTip = "Opacity in the composite (0 %: the layer opens on its own)";
         row.add( check );
         row.add( mode );
         row.addStretch();
         row.add( opacity );
         this.sizer.add( row );
         this.rows.push( { name: filter.name, check: check, opacity: opacity } );
      }
      let buttons = new HorizontalSizer;
      buttons.spacing = 8;
      let defaults = new PushButton( this );
      defaults.text = "AEL defaults";
      defaults.toolTip = "AEL's three default layers, at their opacities: NRGF, edge-aware WOW and ACHF 1–16 px";
      defaults.onClick = function() { dialog.set( aelWorkflowDefaultFilters() ); };
      let all = new PushButton( this );
      all.text = "All 16";
      all.toolTip = "Every filter as a layer; only those with an opacity go into the composite";
      all.onClick = function()
      {
         for ( let i = 0; i < dialog.rows.length; ++i )
            dialog.rows[i].check.checked = true;
      };
      let ok = new PushButton( this );
      ok.text = "OK";
      ok.defaultButton = true;
      ok.onClick = function()
      {
         let picked = dialog.read();
         if ( picked.filters.length == 0 )
         {
            new MessageBox( "Tick at least one filter.", "Advanced settings", StdIcon.Warning, StdButton.Ok ).execute();
            return;
         }
         dialog.choice = picked;
         dialog.ok();
      };
      let cancel = new PushButton( this );
      cancel.text = "Cancel";
      cancel.onClick = function() { dialog.cancel(); };
      buttons.add( defaults );
      buttons.add( all );
      buttons.addStretch();
      buttons.add( ok );
      buttons.add( cancel );
      this.sizer.add( buttons );
      this.defaultsButton = defaults;
      this.allButton = all;
      this.okButton = ok;
      this.cancelButton = cancel;
      this.adjustToContents();
   }

   set( choice )
   {
      for ( let i = 0; i < this.rows.length; ++i )
      {
         let row = this.rows[i];
         row.check.checked = choice.filters.indexOf( row.name ) >= 0;
         row.opacity.value = Math.round( 100 * ( choice.opacities[row.name] || 0 ) );
      }
   }

   read()
   {
      let choice = { filters: [], opacities: {} };
      for ( let i = 0; i < this.rows.length; ++i )
         if ( this.rows[i].check.checked )
         {
            choice.filters.push( this.rows[i].name );
            choice.opacities[this.rows[i].name] = this.rows[i].opacity.value / 100;
         }
      choice.filters = aelWorkflowOrdered( choice.filters );
      return choice;
   }
};

// The filters chosen, in one line: each layer that goes into the composite with its opacity, and how many open on their
// own.
function aelBridgeChoiceText( choice )
{
   let parts = [], alone = 0;
   for ( let i = 0; i < AEL_FILTERS.length; ++i )
   {
      let filter = AEL_FILTERS[i];
      if ( choice.filters.indexOf( filter.name ) < 0 )
         continue;
      let opacity = Math.round( 100 * ( choice.opacities[filter.name] || 0 ) );
      if ( opacity > 0 )
         parts.push( filter.label.replace( /^\d+[a-z]? /, "" ) + " " + opacity + "\u00a0%" );   // number and % together
      else
         ++alone;
   }
   return "Filter layers: " + ( parts.length ? parts.join( ", " ) : "none in the composite" )
          + ( alone ? ", and " + alone + " more on " + ( alone == 1 ? "its" : "their" ) + " own" : "" );
}

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
      this.darks = [];
      this.flats = [];
      // AEL's three default layers unless the advanced settings choose others
      this.choice = aelWorkflowDefaultFilters();
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
         [ "Make:", "Image:", "Totality RAW photos:", "Darks (optional):", "Flats (optional):", "Output folder:" ].map(
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

      // What to make, and what that does
      let modeSizer = new HorizontalSizer;
      modeSizer.spacing = 6;
      this.modeList = new ComboBox( this );
      for ( let i = 0; i < AEL_OPERATIONS.length; ++i )
         this.modeList.addItem( AEL_OPERATIONS[i] );
      this.modeList.toolTip = "<p>What AEL makes:</p><ul>" + AEL_OPERATIONS.map( function( name, i )
         {
            return "<li><b>" + name + ".</b> " + AEL_OPERATION_HELP[i] + "</li>";
         } ).join( "" ) + "</ul>";
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
      let helpSizer = new HorizontalSizer;
      helpSizer.addSpacing( captionWidth + this.logicalPixelsToPhysical( 6 ) );
      this.modeHelp = new Label( this );
      this.modeHelp.wordWrapping = true;
      this.modeHelp.styleSheet = "QLabel { color: gray; }";
      helpSizer.add( this.modeHelp, 100 );
      this.sizer.add( helpSizer );

      // From RAW photos: the totality and, if there are any, its darks and its flats. Each list takes several files at
      // once, in one container that hides as a whole; a file that is not RAW is not added.
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
               for ( let i = 0; i < chooser.filePaths.length; ++i )
               {
                  let path = chooser.filePaths[i];
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
      let darks = fileList( "Darks (optional):", "darks", 50, "Dark frames of the same camera",
                            "Dark frames of the same camera and ISO, with the lens covered: AEL makes a master dark for each "
                            + "exposure of the photos. One that is not a dark is left out, and the receipt says why." );
      let flats = fileList( "Flats (optional):", "flats", 50, "Flat frames of the same camera and optics",
                            "Flat frames of the same camera and optics, of an even light: AEL makes a master flat. It removes "
                            + "the vignetting and the dust shadows. One that is not a flat is left out, and the receipt "
                            + "says why." );
      this.rawText = raw.list;
      this.addRawButton = raw.add;
      this.darksText = darks.list;
      this.addDarksButton = darks.add;
      this.flatsText = flats.list;
      this.addFlatsButton = flats.add;

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

      // The filter layers: AEL's defaults, or what the advanced settings choose
      let filtersSizer = new HorizontalSizer;
      filtersSizer.spacing = 6;
      filtersSizer.addSpacing( captionWidth + this.logicalPixelsToPhysical( 6 ) );
      this.choiceLabel = new Label( this );
      this.choiceLabel.wordWrapping = true;
      this.advancedButton = new PushButton( this );
      this.advancedButton.text = "Advanced settings…";
      this.advancedButton.toolTip = "Choose other filters than AEL's three default layers, and their opacities";
      this.advancedButton.onClick = function()
      {
         let settings = new AELFiltersDialog( dialog.choice );
         if ( settings.execute() )
         {
            dialog.choice = settings.choice;
            dialog.updateChoice();
         }
      };
      filtersSizer.add( this.choiceLabel, 100 );
      filtersSizer.add( this.advancedButton );
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

      // The whole library, for whoever wants more than this dialog
      let moreSizer = new HorizontalSizer;
      moreSizer.spacing = 6;
      let more = new Label( this );
      more.wordWrapping = true;
      more.styleSheet = "QLabel { color: gray; }";
      more.text = "For more faithful results and more filters, try the whole Agentic Eclipse Library with an AI agent.";
      let github = new ToolButton( this );
      github.text = "GitHub";
      github.toolTip = AEL_GITHUB_URL;
      github.onClick = function() { aelBridgeOpenUrl( AEL_GITHUB_URL ); };
      moreSizer.add( more, 100 );
      moreSizer.add( github );
      this.sizer.add( moreSizer );
      this.moreLabel = more;
      this.githubButton = github;

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
         this.darksText.text = names( this.darks );
         this.flatsText.text = names( this.flats );
      };
      this.updateChoice = function()
      {
         this.choiceLabel.text = aelBridgeChoiceText( this.choice );
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
         this.choiceLabel.visible = mode == 0 || mode == 3;
         this.advancedButton.visible = mode == 0 || mode == 3;
         this.modeHelp.text = AEL_OPERATION_HELP[mode];
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
            {
               // the Photoshop connector's closing message, also written to the Process Console
               let result = aelWorkflowRaw( d.raw, d.darks, d.flats, outputRoot, d.pythonPath, d.aelRoot,
                                            d.buildComposite, d.choice );
               new MessageBox( aelWorkflowDoneMessage( result ), "Agentic Eclipse Library", StdIcon.Information,
                               StdButton.Ok ).execute();
            }
            else if ( mode <= 2 )
               aelBridgeRunOnView( { view: d.targetView, mode: mode == 1 ? "structure" : "polar", geometry: null,
                                     outputDirectory: outputRoot, pythonPath: d.pythonPath, aelRoot: d.aelRoot,
                                     rmax: parseFloat( d.rmaxEdit.text ) } );
            else
               aelWorkflowFiltersFromView( d.targetView, outputRoot, d.choice, d.pythonPath, d.aelRoot,
                                           d.buildComposite );
         }
         catch ( error )
         {
            Console.criticalln( "Agentic Eclipse Library: " + error );
            new MessageBox( String( error ), "Agentic Eclipse Library", StdIcon.Error, StdButton.Ok ).execute();
         }
      };

      this.updateChoice();
      this.updateOperation();
      this.adjustToContents();
   }
};
