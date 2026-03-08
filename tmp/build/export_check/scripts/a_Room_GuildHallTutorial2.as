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
   
   [Embed(source="/_assets/assets.swf", symbol="symbol2145")]
   public dynamic class a_Room_GuildHallTutorial2 extends MovieClip
   {
      
      public var am_CollisionObject:MovieClip;
      
      public var am_Parrot:ac_IntroParrot;
      
      public var am_Jumpers:MovieClip;
      
      public var am_MonsterGroup:MovieClip;
      
      public var cutscene:Array;
      
      public var closingSkit:Array;
      
      public var parrotLeave:Array;
      
      public var bGoblinsAlerted:Boolean;
      
      public var bGoblinsCleared:Boolean;
      
      public var bParrotCleared:Boolean;
      
      public function a_Room_GuildHallTutorial2()
      {
         super();
         addFrameScript(0,this.frame1);
         this.__setProp_am_Parrot_a_Room_GuildHallTutorial2_Cues_0();
      }
      
      public function InitRoom(param1:a_GameHook) : void
      {
         this.bGoblinsAlerted = this.bGoblinsCleared = this.bParrotCleared = false;
         var _loc3_:uint = uint(this.am_MonsterGroup.numChildren);
         var _loc4_:Number = 0;
         while(_loc4_ < _loc3_)
         {
            var _loc2_:a_Cue = this.am_MonsterGroup.getChildAt(_loc4_) as a_Cue;
            null.sleepAnim = "Sitting";
            _loc4_++;
         }
         _loc3_ = uint(this.am_Jumpers.numChildren);
         _loc4_ = 0;
         while(_loc4_ < _loc3_)
         {
            _loc2_ = this.am_Jumpers.getChildAt(_loc4_) as a_Cue;
            null.bHoldSpawn = true;
            null.dramaAnim = "Board";
            _loc4_++;
         }
         param1.SetPhase(this.UpdateRoom);
      }
      
      public function HasEngaged(param1:MovieClip) : Boolean
      {
         var _loc2_:a_Cue = null;
         var _loc3_:uint = uint(param1.numChildren);
         var _loc4_:Number = 0;
         while(_loc4_ < _loc3_)
         {
            _loc2_ = param1.getChildAt(_loc4_) as a_Cue;
            if(_loc2_.Health() != 1)
            {
               return true;
            }
            _loc4_++;
         }
         return false;
      }
      
      public function UpdateRoom(param1:a_GameHook) : void
      {
         var _loc2_:a_Cue = null;
         var _loc3_:* = 0;
         var _loc4_:Number = 0;
         if(!this.bGoblinsAlerted)
         {
            if(param1.OnTrigger("am_Trigger_01") || this.HasEngaged(this.am_MonsterGroup))
            {
               this.am_MonsterGroup.am_Leader.Skit("<GetUp>");
               param1.PlayScript(this.cutscene);
               this.bGoblinsAlerted = true;
            }
         }
         if(param1.OnScriptFinish(this.cutscene))
         {
            _loc3_ = uint(this.am_MonsterGroup.numChildren);
            _loc4_ = 0;
            while(_loc4_ < _loc3_)
            {
               _loc2_ = this.am_MonsterGroup.getChildAt(_loc4_) as a_Cue;
               if(_loc2_.name != "am_Leader")
               {
                  _loc2_.Skit("<GetUp>");
               }
               _loc4_++;
            }
            this.am_Parrot.Skit("<Scared>");
            param1.SetPhase(this.UpdateRoomPhase2);
         }
      }
      
      public function UpdateRoomPhase2(param1:a_GameHook) : void
      {
         if(param1.AtTime(1500))
         {
            param1.Group(this.am_MonsterGroup).Aggro();
            param1.Group(this.am_Jumpers).Spawn();
         }
         if(param1.AtTime(2000))
         {
            this.am_Parrot.SetAnimation("Run");
            param1.PlayScript(this.parrotLeave);
            this.bParrotCleared = true;
         }
         if(param1.Group(this.am_MonsterGroup).Defeated() && param1.Group(this.am_Jumpers).Defeated())
         {
            param1.PlayScript(this.closingSkit);
            this.bGoblinsCleared = true;
         }
         if(this.bGoblinsCleared && this.bParrotCleared)
         {
            param1.SetPhase(null);
         }
      }
      
      internal function __setProp_am_Parrot_a_Room_GuildHallTutorial2_Cues_0() : *
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
         this.cutscene = ["3 Leader <PullLever> Look out!"];
         this.closingSkit = ["2 Player Great, these things are everywhere..."];
         this.parrotLeave = ["0 Parrot <Goto Red 1>","5 RemoveCue Parrot"];
      }
   }
}

