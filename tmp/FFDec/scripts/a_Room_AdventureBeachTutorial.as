package
{
   import adobe.utils.*;
   import flash.accessibility.*;
   import flash.desktop.*;
   import flash.display.*;
   import flash.errors.*;
   import flash.events.*;
   import flash.external.*;
   import flash.filters.*;
   import flash.geom.*;
   import flash.globalization.*;
   import flash.media.*;
   import flash.net.*;
   import flash.net.drm.*;
   import flash.printing.*;
   import flash.profiler.*;
   import flash.sampler.*;
   import flash.sensors.*;
   import flash.system.*;
   import flash.text.*;
   import flash.text.engine.*;
   import flash.text.ime.*;
   import flash.ui.*;
   import flash.utils.*;
   import flash.xml.*;
   
   [Embed(source="/_assets/assets.swf", symbol="symbol2103")]
   public dynamic class a_Room_AdventureBeachTutorial extends MovieClip
   {
      public var am_CollisionObject:MovieClip;
      
      public var am_Parrot:ac_IntroParrot;
      
      public var am_MonsterGroup:MovieClip;
      
      public var cutscene:Array;
      
      public function a_Room_AdventureBeachTutorial()
      {
         super();
         addFrameScript(0,this.frame1);
         this.__setProp_am_Parrot_a_Room_AdventureBeachTutorial_ParrotSetUp_0();
      }
      
      public function InitRoom(param1:a_GameHook) : void
      {
         param1.SetPhase(this.UpdateRoom);
      }
      
      public function UpdateRoom(param1:a_GameHook) : void
      {
         if(param1.AtTime(0))
         {
            param1.PlayScript(this.cutscene);
         }
         if(param1.AtTime(3750))
         {
            this.am_Parrot.SetAnimation("Run");
            param1.SetPhase(null);
         }
      }
      
      internal function __setProp_am_Parrot_a_Room_AdventureBeachTutorial_ParrotSetUp_0() : *
      {
         try
         {
            this.am_Parrot["componentInspectorSetting"] = true;
         }
         catch(e:Error)
         {
         }
         this.am_Parrot.characterName = "";
         this.am_Parrot.displayName = "";
         this.am_Parrot.dramaAnim = "";
         this.am_Parrot.itemDrop = "";
         this.am_Parrot.sayOnActivate = "";
         this.am_Parrot.sayOnAlert = "";
         this.am_Parrot.sayOnBloodied = "";
         this.am_Parrot.sayOnDeath = "";
         this.am_Parrot.sayOnInteract = "";
         this.am_Parrot.sayOnSpawn = "";
         this.am_Parrot.sleepAnim = "";
         this.am_Parrot.team = "neutral";
         this.am_Parrot.waitToAggro = 0;
         try
         {
            this.am_Parrot["componentInspectorSetting"] = false;
         }
         catch(e:Error)
         {
         }
      }
      
      internal function frame1() : *
      {
         this.cutscene = ["11 Parrot <Panic> The keep is this way!","4 Parrot <Goto Red 1>","5 RemoveCue Parrot"];
      }
   }
}

