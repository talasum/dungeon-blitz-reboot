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
   
   [Embed(source="/_assets/assets.swf", symbol="symbol2192")]
   public dynamic class a_Room_MainTutorial extends MovieClip
   {
      public var am_CollisionObject:MovieClip;
      
      public var am_LastGuy:ac_GoblinDagger;
      
      public var am_Boss:ac_GoblinShamanHood;
      
      public var am_Parrot:ac_IntroParrot;
      
      public var am_MonsterGroup:MovieClip;
      
      public var am_OldManTutorial:ac_NPCHomeGemMerchant;
      
      public var spawnIndex:uint;
      
      public var numMonsters:uint;
      
      public var monsterList:Vector.<a_Cue>;
      
      public var bIntroStarted:Boolean = false;
      
      public function a_Room_MainTutorial()
      {
         super();
         addFrameScript(0,this.frame1);
         this.__setProp_am_Parrot_a_Room_MainTutorial_Road_0();
         this.__setProp_am_Boss_a_Room_MainTutorial_Boss_0();
         this.__setProp_am_OldManTutorial_a_Room_MainTutorial_Boss_0();
      }
      
      public function InitRoom(param1:a_GameHook) : void
      {
         var _loc2_:a_Cue = null;
         this.bIntroStarted = false;
         this.am_Boss.displayName = "Ranik, The Geomancer";
         this.am_Boss.visible = false;
         this.am_Boss.bHoldSpawn = true;
         this.am_Boss["entType"] = "IntroGoblinShamanHood";
         param1.initialPhase = this.UpdateRoom;
         this.am_LastGuy.characterName = "am_LastGuy";
         this.am_LastGuy.AddBuff("Untouchable");
         this.am_Boss.AddBuff("Untouchable");
         param1.bossFightBeginsWhenThisGuyIsDead = "am_LastGuy";
         this.numMonsters = this.am_MonsterGroup.numChildren;
         this.monsterList = new Vector.<a_Cue>(this.numMonsters,true);
         var _loc3_:Number = 0;
         while(_loc3_ < this.numMonsters)
         {
            _loc2_ = this.am_MonsterGroup.getChildAt(_loc3_) as a_Cue;
            _loc2_.bHoldSpawn = true;
            _loc2_.dramaAnim = "Board";
            this.monsterList[_loc3_] = _loc2_;
            _loc3_++;
         }
         this.spawnIndex = 0;
         param1.cutSceneStartBoss = ["0 Camera 1","5 OldManTutorial Thank the stars you\'re here!","14 OldManTutorial The goblins have ruined the keep.","14 OldManTutorial I was the caretaker here...","6 Parrot <Goto Red 1> Look out!","4 Boss <Goto Red 2> Stop the human!","10 Boss Don\'t let him|her take our home!","6 Camera Free"];
         param1.cutSceneDefeatBoss = ["0 Shake 15","8 OldManTutorial Good gravy what a mess.","10 OldManTutorial Let\'s say we clean this place up.","10 Parrot This place is a dump...","6 OldManTutorial Then we best get to work!","1 Parrot <Panic>","8 End"];
      }
      
      public function UpdateRoom(param1:a_GameHook) : void
      {
         if(this.bIntroStarted)
         {
            return;
         }
         if(param1.OnTrigger("am_Trigger_01") || !this.am_LastGuy.Health())
         {
            this.bIntroStarted = true;
            this.am_LastGuy.Kill();
            this.am_Boss.Spawn();
            this.am_Boss.DeepSleep();
            param1.PlayScript(param1.cutSceneStartBoss);
            param1.bossFightPhase = this.UpdateBossFight;
         }
      }
      
      public function UpdateBossFight(param1:a_GameHook) : void
      {
         if(!param1.OnScriptFinish(param1.cutSceneStartBoss))
         {
            return;
         }
         param1.SetPhase(this.UpdateBossRevealDelay);
      }

      public function UpdateBossRevealDelay(param1:a_GameHook) : void
      {
         if(!param1.AtTime(5000))
         {
            return;
         }
         this.am_Boss.visible = true;
         this.am_Boss.RemoveBuff("Untouchable");
         this.am_Boss.Aggro();
         param1.Group(this.am_MonsterGroup).Spawn();
         param1.Group(this.am_MonsterGroup).Aggro();
         param1.SetPhase(this.UpdateBossCombat);
      }

      public function UpdateBossCombat(param1:a_GameHook) : void
      {
         var _loc2_:a_Cue = null;
         var _loc3_:Number = 0;
         if(this.am_Boss.Defeated())
         {
            param1.Group(this.am_MonsterGroup).Kill();
            this.monsterList = null;
            param1.SetPhase(null);
            return;
         }
         if(param1.AtTimeRepeat(2000,0))
         {
            _loc3_ = 0;
            while(_loc3_ < this.numMonsters)
            {
               _loc2_ = this.monsterList[_loc3_];
               if(!_loc2_.Health())
               {
                  _loc2_.Remove();
                  _loc2_.Spawn();
                  _loc2_.Aggro();
               }
               _loc3_++;
            }
         }
      }
      
      internal function __setProp_am_Parrot_a_Room_MainTutorial_Road_0() : *
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
      
      internal function __setProp_am_Boss_a_Room_MainTutorial_Boss_0() : *
      {
         try
         {
            this.am_Boss["componentInspectorSetting"] = true;
         }
         catch(e:Error)
         {
         }
         this.am_Boss.characterName = ",IntroGoblinShamanHood";
         this.am_Boss.displayName = "";
         this.am_Boss.dramaAnim = "";
         this.am_Boss.itemDrop = "";
         this.am_Boss.sayOnActivate = "";
         this.am_Boss.sayOnAlert = "";
         this.am_Boss.sayOnBloodied = "";
         this.am_Boss.sayOnDeath = "";
         this.am_Boss.sayOnInteract = "";
         this.am_Boss.sayOnSpawn = "";
         this.am_Boss.sleepAnim = "";
         this.am_Boss.team = "default";
         this.am_Boss.waitToAggro = 0;
         try
         {
            this.am_Boss["componentInspectorSetting"] = false;
         }
         catch(e:Error)
         {
         }
      }
      
      internal function __setProp_am_OldManTutorial_a_Room_MainTutorial_Boss_0() : *
      {
         try
         {
            this.am_OldManTutorial["componentInspectorSetting"] = true;
         }
         catch(e:Error)
         {
         }
         this.am_OldManTutorial.characterName = "";
         this.am_OldManTutorial.displayName = "";
         this.am_OldManTutorial.dramaAnim = "";
         this.am_OldManTutorial.itemDrop = "";
         this.am_OldManTutorial.sayOnActivate = "";
         this.am_OldManTutorial.sayOnAlert = "";
         this.am_OldManTutorial.sayOnBloodied = "";
         this.am_OldManTutorial.sayOnDeath = "";
         this.am_OldManTutorial.sayOnInteract = "";
         this.am_OldManTutorial.sayOnSpawn = "";
         this.am_OldManTutorial.sleepAnim = "";
         this.am_OldManTutorial.team = "neutral";
         this.am_OldManTutorial.waitToAggro = 0;
         try
         {
            this.am_OldManTutorial["componentInspectorSetting"] = false;
         }
         catch(e:Error)
         {
         }
      }
      
      internal function frame1() : *
      {
      }
   }
}

