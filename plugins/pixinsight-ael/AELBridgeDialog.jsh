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
      this.scaledMinWidth = 560;

      let active = ImageWindow.activeWindow;
      this.targetView = active.isNull ? undefined : active.mainView;
      // Not shown: the Python is found by the connector (the one that worked last is tried first) and AEL is the one that
      // comes with it. A script or a test may set them before Run.
      this.pythonPath = Settings.read( AEL_BRIDGE_SETTINGS_KEY + "pythonPath", DataType.UTF8String ) || "";
      this.aelRoot = aelBridgeInitialRoot();

      let intro = new Label( this );
      intro.wordWrapping = true;
      intro.useRichText = true;
      intro.text = "<b>Agentic Eclipse Library</b><br>A structure image or an unrolled view of the corona, made from the "
                   + "selected image. AEL finds the Moon on the image by itself; the image is not changed, and the results "
                   + "open in new windows, with one that shows the circle it found.";
      this.sizer = new VerticalSizer;
      this.sizer.margin = 10;
      this.sizer.spacing = 8;
      this.sizer.add( intro );

      let imageSizer = new HorizontalSizer;
      imageSizer.spacing = 6;
      let imageLabel = new Label( this );
      imageLabel.text = "Image:";
      imageLabel.setScaledFixedWidth( 90 );
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
      modeLabel.setScaledFixedWidth( 90 );
      this.modeList = new ComboBox( this );
      this.modeList.addItem( "structure" );
      this.modeList.addItem( "polar" );
      let rmaxLabel = new Label( this );
      rmaxLabel.text = "Radius (solar radii):";
      this.rmaxEdit = new Edit( this );
      this.rmaxEdit.text = "4.0";
      this.rmaxEdit.setScaledFixedWidth( 64 );
      operationSizer.add( modeLabel );
      operationSizer.add( this.modeList );
      operationSizer.addStretch();
      operationSizer.add( rmaxLabel );
      operationSizer.add( this.rmaxEdit );
      this.sizer.add( operationSizer );
      // The radius belongs to the unrolled view only.
      this.updateOperation = function()
      {
         let polar = this.modeList.currentItem == 1;
         rmaxLabel.visible = polar;
         this.rmaxEdit.visible = polar;
      };
      this.modeList.onItemSelected = function() { this.dialog.updateOperation(); };

      let outputSizer = new HorizontalSizer;
      outputSizer.spacing = 6;
      let outputLabel = new Label( this );
      outputLabel.text = "Output folder:";
      outputLabel.setScaledFixedWidth( 90 );
      this.outputEdit = new Edit( this );
      let saved = Settings.read( AEL_BRIDGE_SETTINGS_KEY + "outputDirectory", DataType.UTF8String );
      if ( saved )
         this.outputEdit.text = saved;
      let outputButton = new ToolButton( this );
      outputButton.icon = this.scaledResource( ":/icons/select-folder.png" );
      outputButton.setScaledFixedSize( 24, 24 );
      outputButton.onClick = function()
      {
         let chooser = new GetDirectoryDialog;
         chooser.caption = "Output folder";
         if ( this.dialog.outputEdit.text.length > 0 )
            chooser.initialPath = this.dialog.outputEdit.text;
         if ( chooser.execute() )
            this.dialog.outputEdit.text = chooser.directory;
      };
      outputSizer.add( outputLabel );
      outputSizer.add( this.outputEdit, 100 );
      outputSizer.add( outputButton );
      this.sizer.add( outputSizer );

      let buttons = new HorizontalSizer;
      buttons.spacing = 8;
      let runButton = new PushButton( this );
      this.runButton = runButton;
      runButton.text = "Run AEL";
      runButton.defaultButton = true;
      let cancelButton = new PushButton( this );
      cancelButton.text = "Cancel";
      cancelButton.onClick = function() { this.dialog.cancel(); };
      buttons.addStretch();
      buttons.add( runButton );
      buttons.add( cancelButton );
      this.sizer.add( buttons );

      runButton.onClick = function()
      {
         try
         {
            if ( !this.dialog.targetView )
               throw new Error( "Select an image." );
            let parameters = {
               view: this.dialog.targetView,
               mode: this.dialog.modeList.currentItem == 0 ? "structure" : "polar",
               geometry: null,                              // measured by AEL on the image
               outputDirectory: this.dialog.outputEdit.text.trim(),
               pythonPath: this.dialog.pythonPath,
               aelRoot: this.dialog.aelRoot,
               rmax: parseFloat( this.dialog.rmaxEdit.text )
            };
            Settings.write( AEL_BRIDGE_SETTINGS_KEY + "outputDirectory", DataType.UTF8String, parameters.outputDirectory );
            this.dialog.ok();
            aelBridgeRunOnView( parameters );
         }
         catch ( error )
         {
            Console.criticalln( "AEL bridge: " + error );
            new MessageBox( String( error ), "Agentic Eclipse Library", StdIcon.Error, StdButton.Ok ).execute();
         }
      };

      this.updateOperation();
      this.adjustToContents();
   }
};
