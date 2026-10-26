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

var AELBridgeDialog = class extends Dialog
{
   constructor()
   {
      super();
   this.windowTitle = "Agentic Eclipse Library";
   this.userResizable = true;
   this.scaledMinWidth = 720;

   let active = ImageWindow.activeWindow;
   this.targetView = active.isNull ? undefined : active.mainView;
   this.geometry = null;

   let intro = new Label( this );
   intro.wordWrapping = true;
   intro.useRichText = true;
   intro.text = "<b>AEL bridge</b><br>Runs the fixed <i>structure</i> or <i>polar</i> recipe in Python. "
                + "The source image is read only; every result opens in a new window and is saved with its receipt.";
   this.sizer = new VerticalSizer;
   this.sizer.margin = 10;
   this.sizer.spacing = 8;
   this.sizer.add( intro );

   let imageSizer = new HorizontalSizer;
   imageSizer.spacing = 6;
   let imageLabel = new Label( this );
   imageLabel.text = "Image:";
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

   let operationSizer = new HorizontalSizer;
   operationSizer.spacing = 6;
   let modeLabel = new Label( this );
   modeLabel.text = "Operation:";
   this.modeList = new ComboBox( this );
   this.modeList.addItem( "structure" );
   this.modeList.addItem( "polar" );
   let rmaxLabel = new Label( this );
   rmaxLabel.text = "Polar radius (solar radii):";
   this.rmaxEdit = new Edit( this );
   this.rmaxEdit.text = "4.0";
   this.rmaxEdit.setScaledFixedWidth( 64 );
   operationSizer.add( modeLabel );
   operationSizer.add( this.modeList );
   operationSizer.addStretch();
   operationSizer.add( rmaxLabel );
   operationSizer.add( this.rmaxEdit );
   this.sizer.add( operationSizer );

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
            let dialog = new GetDirectoryDialog;
            dialog.caption = label;
            if ( edit.text.length > 0 )
               dialog.initialPath = edit.text;
            if ( dialog.execute() )
               edit.text = dialog.directory;
         }
         else
         {
            let dialog = new OpenFileDialog;
            dialog.caption = label;
            dialog.multiple = false;
            if ( dialog.execute() )
               edit.text = dialog.fileName;
         }
      };
      row.add( caption );
      row.add( edit, 100 );
      row.add( button );
      parent.sizer.add( row );
      return edit;
   }

   this.outputEdit = pathRow( this, "Output folder:", true );
   this.pythonEdit = pathRow( this, "Python executable:", false );
   this.aelRootEdit = pathRow( this, "AEL folder (optional):", true );
   this.geometryFileEdit = pathRow( this, "Geometry JSON:", false );
   this.validMaskEdit = pathRow( this, "Valid mask (optional):", false );

   let savedPython = Settings.read( AEL_BRIDGE_SETTINGS_KEY + "pythonPath", DataType.UTF8String );
   if ( savedPython )
      this.pythonEdit.text = savedPython;
   let savedRoot = Settings.read( AEL_BRIDGE_SETTINGS_KEY + "aelRoot", DataType.UTF8String );
   if ( savedRoot )
      this.aelRootEdit.text = savedRoot;
   let savedOutput = Settings.read( AEL_BRIDGE_SETTINGS_KEY + "outputDirectory", DataType.UTF8String );
   if ( savedOutput )
      this.outputEdit.text = savedOutput;

   let geometryBox = new GroupBox( this );
   geometryBox.title = "Geometry (image coordinates: x right, y down)";
   geometryBox.sizer = new VerticalSizer;
   geometryBox.sizer.margin = 8;
   geometryBox.sizer.spacing = 5;
   this.sizer.add( geometryBox );

   this.geometryEdits = {};
   function geometryRow( parent, entries )
   {
      let row = new HorizontalSizer;
      row.spacing = 5;
      for ( let i = 0; i < entries.length; ++i )
      {
         let key = entries[i][0];
         let label = new Label( parent );
         label.text = entries[i][1];
         let edit = new Edit( parent );
         edit.setScaledMinWidth( 88 );
         parent.dialog.geometryEdits[key] = edit;
         row.add( label );
         row.add( edit, 100 );
         if ( i + 1 < entries.length )
            row.addSpacing( 10 );
      }
      parent.sizer.add( row );
   }
   geometryRow( geometryBox, [ [ "sunX", "Sun x:" ], [ "sunY", "Sun y:" ], [ "sunRadius", "Sun radius:" ] ] );
   geometryRow( geometryBox, [ [ "moonX", "Moon x:" ], [ "moonY", "Moon y:" ], [ "moonRadius", "Moon radius:" ] ] );
   geometryRow( geometryBox, [ [ "north", "North (deg):" ], [ "arcsec", "Arcsec/pixel:" ] ] );
   this.geometryEdits.north.text = "0";

   let geometryOptions = new HorizontalSizer;
   geometryOptions.spacing = 6;
   this.mirroredCheck = new CheckBox( geometryBox );
   this.mirroredCheck.text = "Mirrored image";
   let noteLabel = new Label( geometryBox );
   noteLabel.text = "Note:";
   this.noteEdit = new Edit( geometryBox );
   let loadButton = new PushButton( geometryBox );
   loadButton.text = "Load JSON";
   loadButton.onClick = function()
   {
      let path = this.dialog.geometryFileEdit.text.trim();
      if ( path.length == 0 )
      {
         let chooser = new OpenFileDialog;
         chooser.caption = "Load AEL geometry JSON";
         chooser.filters = [ [ "JSON", ".json" ] ];
         if ( !chooser.execute() )
            return;
         path = chooser.fileName;
         this.dialog.geometryFileEdit.text = path;
      }
      try
      {
         let geometry = JSON.parse( File.readTextFile( path ) );
         let edits = this.dialog.geometryEdits;
         edits.sunX.text = String( geometry.sun_xy[0] );
         edits.sunY.text = String( geometry.sun_xy[1] );
         edits.sunRadius.text = String( geometry.sun_radius_px );
         edits.moonX.text = geometry.moon_xy == null ? "" : String( geometry.moon_xy[0] );
         edits.moonY.text = geometry.moon_xy == null ? "" : String( geometry.moon_xy[1] );
         edits.moonRadius.text = geometry.moon_radius_px == null ? "" : String( geometry.moon_radius_px );
         edits.north.text = String( geometry.north_deg == null ? 0 : geometry.north_deg );
         edits.arcsec.text = geometry.arcsec_per_px == null ? "" : String( geometry.arcsec_per_px );
         this.dialog.mirroredCheck.checked = geometry.mirrored == true;
         this.dialog.noteEdit.text = geometry.note || "";
      }
      catch ( error )
      {
         new MessageBox( "Could not load geometry:\n" + error, "AEL bridge", StdIcon.Error, StdButton.Ok ).execute();
      }
   };
   geometryOptions.add( this.mirroredCheck );
   geometryOptions.addSpacing( 12 );
   geometryOptions.add( noteLabel );
   geometryOptions.add( this.noteEdit, 100 );
   geometryOptions.add( loadButton );
   geometryBox.sizer.add( geometryOptions );

   let buttons = new HorizontalSizer;
   buttons.spacing = 8;
   let runButton = new PushButton( this );
   runButton.text = "Run AEL";
   runButton.defaultButton = true;
   let cancelButton = new PushButton( this );
   cancelButton.text = "Cancel";
   cancelButton.onClick = function() { this.dialog.cancel(); };
   buttons.addStretch();
   buttons.add( runButton );
   buttons.add( cancelButton );
   this.sizer.add( buttons );

   this.geometryFromDialog = function()
   {
      let edits = this.geometryEdits;
      function required( value, name )
      {
         let number = parseFloat( value );
         if ( !isFinite( number ) )
            throw new Error( name + " must be a number." );
         return number;
      }
      function optional( value, name )
      {
         return value.trim().length == 0 ? null : required( value, name );
      }
      let geometry = {
         shape: [ this.targetView.image.height, this.targetView.image.width ],
         sun_xy: [ required( edits.sunX.text, "Sun x" ), required( edits.sunY.text, "Sun y" ) ],
         sun_radius_px: required( edits.sunRadius.text, "Sun radius" ),
         moon_xy: null,
         moon_radius_px: null,
         north_deg: required( edits.north.text, "North" ),
         mirrored: this.mirroredCheck.checked,
         arcsec_per_px: optional( edits.arcsec.text, "Arcsec/pixel" ),
         note: this.noteEdit.text
      };
      let mx = optional( edits.moonX.text, "Moon x" );
      let my = optional( edits.moonY.text, "Moon y" );
      let mr = optional( edits.moonRadius.text, "Moon radius" );
      if ( mx != null || my != null || mr != null )
      {
         if ( mx == null || my == null || mr == null )
            throw new Error( "Complete all Moon fields or leave all of them empty." );
         geometry.moon_xy = [ mx, my ];
         geometry.moon_radius_px = mr;
      }
      return geometry;
   };

   runButton.onClick = function()
   {
      try
      {
         if ( !this.dialog.targetView )
            throw new Error( "Select an image." );
         let parameters = {
            view: this.dialog.targetView,
            mode: this.dialog.modeList.currentItem == 0 ? "structure" : "polar",
            geometry: this.dialog.geometryFromDialog(),
            outputDirectory: this.dialog.outputEdit.text.trim(),
            pythonPath: this.dialog.pythonEdit.text.trim(),
            aelRoot: this.dialog.aelRootEdit.text.trim(),
            validMask: this.dialog.validMaskEdit.text.trim(),
            rmax: parseFloat( this.dialog.rmaxEdit.text )
         };
         Settings.write( AEL_BRIDGE_SETTINGS_KEY + "aelRoot", DataType.UTF8String, parameters.aelRoot );
         Settings.write( AEL_BRIDGE_SETTINGS_KEY + "outputDirectory", DataType.UTF8String, parameters.outputDirectory );
         this.dialog.ok();
         aelBridgeRunOnView( parameters );
      }
      catch ( error )
      {
         Console.criticalln( "AEL bridge: " + error );
         new MessageBox( String( error ), "AEL bridge", StdIcon.Error, StdButton.Ok ).execute();
      }
   };

   this.adjustToContents();
   }
}
