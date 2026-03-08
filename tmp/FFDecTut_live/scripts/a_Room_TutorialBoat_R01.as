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
   
   [Embed(source="/_assets/assets.swf", symbol="symbol160")]
   public dynamic class a_Room_TutorialBoat_R01 extends MovieClip
   {
      
      public var am_GStub5:ac_IntroGoblinDagger;
      
      public var am_Foreground_THEAD:MovieClip;
      
      public var am_Cloud8:a_Animation_EB_BoatCloud02;
      
      public var am_LastMonster:ac_IntroGoblinDagger;
      
      public var am_GStub4:ac_IntroGoblinDagger;
      
      public var am_GStub3:ac_IntroGoblinDagger;
      
      public var am_Goblin0:ac_IntroGoblinDagger;
      
      public var am_TBack:a_Animation_EB_BoatKrakenTentacle01;
      
      public var am_Cloud7:a_Animation_EB_BoatCloud02;
      
      public var am_GStub2:ac_IntroGoblinDagger;
      
      public var am_Goblin1:ac_IntroGoblinClub;
      
      public var am_Cloud6:a_Animation_EB_BoatCloud02;
      
      public var am_CollisionObject:MovieClip;
      
      public var am_GStub1:ac_IntroGoblinClub;
      
      public var am_Goblin2:ac_IntroGoblinDagger;
      
      public var am_Foreground_Splash4:a_Animation_Splash_03;
      
      public var am_Phage6:ac_IntroPsychophageBaby;
      
      public var am_Fink:ac_NPCCaptainSteering;
      
      public var am_Goblin3:ac_IntroGoblinJumper;
      
      public var am_Foreground_Waves:MovieClip;
      
      public var am_Cloud4:a_Animation_EB_BoatCloud01;
      
      public var am_Goblin4:ac_IntroGoblinJumper;
      
      public var am_Cloud3:a_Animation_EB_BoatCloud01;
      
      public var am_Phage4:ac_IntroPsychophageBaby;
      
      public var am_Boss:ac_IntroKraken;
      
      public var am_Goblin5:ac_IntroGoblinJumper;
      
      public var am_Parrot:ac_IntroParrot;
      
      public var am_Foreground_Splash3:a_Animation_Splash_01;
      
      public var am_WaveBGLEFT:a_Animation_EB_BoatWave01;
      
      public var am_Cloud2:a_Animation_EB_BoatCloud01;
      
      public var am_Phage3:ac_IntroDummyFlier;
      
      public var am_Goblin6:ac_IntroGoblinJumper;
      
      public var am_PlayerBoat:a_Animation_BoatPlayer;
      
      public var am_Cloud1:a_Animation_EB_BoatCloud01;
      
      public var am_Cloud10:a_Animation_EB_BoatCloud03;
      
      public var am_Goblin7:ac_IntroGoblinJumper;
      
      public var am_Foreground_TTAIL:MovieClip;
      
      public var am_Cloud11:a_Animation_EB_BoatCloud03;
      
      public var am_Phage1:ac_IntroDummyFlier;
      
      public var am_Cloud12:a_Animation_EB_BoatCloud03;
      
      public var am_Goblin8:ac_IntroGoblinJumper;
      
      public var am_Cloud13:a_Animation_EB_BoatCloud03;
      
      public var am_Goblin9:ac_IntroGoblinJumper;
      
      public var am_Foreground_Hump2:MovieClip;
      
      public var am_Foreground_Hump1:MovieClip;
      
      public var am_WaveBG1:a_Animation_EB_BoatWave01;
      
      public var am_WaveBG2:a_Animation_EB_BoatWave01;
      
      public var am_Lightning1:a_Animation_BoatLightning01;
      
      public var am_Foreground:MovieClip;
      
      public var am_WaveBG3:a_Animation_EB_BoatWave01;
      
      public var am_CloudLEFT:a_Animation_EB_BoatCloud01;
      
      public var am_Lightning2:a_Animation_BoatLightning01;
      
      public var am_Cloud9:a_Animation_EB_BoatCloud02;
      
      public var am_Lightning3:a_Animation_BoatLightning01;
      
      public var Script_BeAlert:Array;
      
      public var Script_OverlayDelay:Array;
      
      public var Script_OverlayDelay2:Array;
      
      public var Script_TheStorm:Array;
      
      public var Script_LookOutFliers:Array;
      
      public var Script_LooksLikeWeAreInTheClear:Array;
      
      public var Script_GoblinWait:Array;
      
      public var Script_Shootem:Array;
      
      public var Script_NicelyDone:Array;
      
      public var Script_VileSeaDemons:Array;
      
      public var Script_LookOut:Array;
      
      public var Script_GoblinWait2:Array;
      
      public var bTutorialVisible:Boolean;

      public var bMoveTutorialShown:Boolean;

      public var moveTutorialShownAt:Number;
      
      public var bWaveTwoActive:Boolean;
      
      public var bWaveThreeActive:Boolean;
      
      public var bWaveFourActive:Boolean;
      
      public function a_Room_TutorialBoat_R01()
      {
         super();
         addFrameScript(0,this.frame1);
         this.__setProp_am_Parrot_a_Room_TutorialBoat_R01_cue_0();
         this.__setProp_am_Goblin3_a_Room_TutorialBoat_R01_cue_0();
         this.__setProp_am_Goblin6_a_Room_TutorialBoat_R01_cue_0();
         this.__setProp_am_Goblin4_a_Room_TutorialBoat_R01_cue_0();
         this.__setProp_am_Goblin7_a_Room_TutorialBoat_R01_cue_0();
         this.__setProp_am_Goblin8_a_Room_TutorialBoat_R01_cue_0();
         this.__setProp_am_Boss_a_Room_TutorialBoat_R01_cue_0();
         this.__setProp_am_Fink_a_Room_TutorialBoat_R01_cue_0();
      }
      
      public function InitRoom(param1:a_GameHook) : void
      {
         this.bMoveTutorialShown = false;
         this.moveTutorialShownAt = 0;
         this.am_Goblin3.bHoldSpawn = true;
         this.am_Goblin4.bHoldSpawn = true;
         this.am_Goblin5.bHoldSpawn = true;
         this.am_Goblin6.bHoldSpawn = true;
         this.am_Goblin7.bHoldSpawn = true;
         this.am_Goblin8.bHoldSpawn = true;
         this.am_Goblin9.bHoldSpawn = true;
         this.am_Phage1.bHoldSpawn = true;
         this.am_Phage3.bHoldSpawn = true;
         this.am_Phage4.bHoldSpawn = true;
         this.am_Phage6.bHoldSpawn = true;
         this.am_TBack.startAnim = "Rise";
         this.am_Foreground_THEAD.am_KrakenBody.startAnim = "Rise";
         this.am_Foreground_TTAIL.am_TFrontLeft.baseAnim = "Ready2";
         this.am_Foreground_TTAIL.am_TFrontLeft.startAnim = "Rise";
         this.am_Foreground_Hump2.am_Hump2.startAnim = "Rise";
         this.am_Foreground_Hump1.am_Hump1.baseAnim = "Ready2";
         this.am_Foreground_Hump1.am_Hump1.startAnim = "Rise";
         this.am_Boss.displayName = "Colossal War Kraken";
         this.am_Boss.bHoldSpawn = true;
         param1.bBossBarOnBottom = false;
         param1.bossFightBeginsWhenThisGuyIsDead = "am_LastMonster";
         param1.bossFightPhase = null;
         param1.initialPhase = this.FirstTickRoom;
         param1.cutSceneStartBoss = ["9 Shake 28","0 Sound NPC_EmberExplosion 1.0","4 Parrot <Scared>^t!?","0 Fink ^t!?","4 Fink Oh no...","8 Shake 28","0 Sound NPC_EmberExplosion 1.0","5 Parrot <Panic>There it is again!","3 Parrot <Goto Red 1>","8 Fink Their Kraken...","4 Parrot <Panic> LOOK OUT!","2 Parrot <Goto Red 4>","2 End"];
         param1.cutSceneDefeatBoss = ["8 Player I told you I\'d protect your ship, Captain.","10 Fink The goblins are running for that coast.","12 Player That\'s the coast of Ellyria. My destination.","10 Fink What?! Ellyria was overrun by the monster hordes fifty years ago.","10 Player My orders are from the King himself.","4 Parrot <Goto Red 1>","4 Parrot I can see a village! A human village","10 Player Human survivors of the Goblin Wars? Impossible!","8 Player Head for that village, Captain.","10 Shake 60","0 Sound NPC_EmberExplosion 1.0","4 Parrot <Panic>Rocks!!!","6 Fink I see \'em. Hold on!","0 Sound FXP_BoatCrash 2.0","10 End"];
      }
      
      public function FirstTickRoom(param1:a_GameHook) : void
      {
         param1.Animate("am_Tint","Off");
         param1.PlayScript(this.Script_TheStorm);
         param1.SetPhase(this.WalkAndTalkPhaseTick);
      }
      
      public function WalkAndTalkPhaseTick(param1:a_GameHook) : void
      {
         if(param1.OnScriptFinish(this.Script_TheStorm))
         {
            if(!this.bMoveTutorialShown)
            {
               param1.ShowTutorial("am_HighlighterMove");
               this.bMoveTutorialShown = true;
               this.moveTutorialShownAt = getTimer();
            }
         }
         if(param1.OnTrigger("am_Trigger_1") || this.bMoveTutorialShown && this.moveTutorialShownAt > 0 && getTimer() - this.moveTutorialShownAt >= 2500)
         {
            param1.HideTutorial("am_HighlighterMove");
            param1.CancelScript(this.Script_TheStorm);
            this.bMoveTutorialShown = false;
            this.moveTutorialShownAt = 0;
            param1.SetPhase(this.PhagePhaseTick);
         }
      }
      
      public function PhagePhaseTick(param1:a_GameHook) : void
      {
         if(param1.AtTime(0))
         {
            param1.PlayScript(this.Script_LookOutFliers);
         }
         if(param1.OnScriptFinish(this.Script_LookOutFliers))
         {
            this.am_Phage1.Spawn();
            this.am_Phage1.Goto("Red 5");
            this.am_Phage1.DeepSleep();
            param1.PlayScript(this.Script_OverlayDelay);
         }
         if(param1.OnScriptFinish(this.Script_OverlayDelay))
         {
            if(!this.am_Phage1.Defeated())
            {
               param1.ShowTutorial("am_HighlighterRanged");
            }
            this.bTutorialVisible = true;
         }
         if(this.am_Phage1.Defeated() && this.bTutorialVisible)
         {
            param1.HideTutorial("am_HighlighterRanged");
            this.bTutorialVisible = false;
            this.am_Phage3.Spawn();
            this.am_Phage3.Goto("Red 7");
            this.bWaveTwoActive = true;
            param1.PlayScript(this.Script_LookOut);
         }
         if(param1.AtTimeRepeat(14000) && this.bWaveTwoActive)
         {
            param1.PlayScript(this.Script_Shootem);
         }
         if(this.am_Phage3.Defeated() && this.bWaveTwoActive)
         {
            this.am_Phage4.Spawn();
            this.am_Phage6.Spawn();
            this.am_Phage4.Goto("Red 5");
            this.am_Phage6.Goto("Red 6");
            this.bWaveTwoActive = false;
            this.bWaveThreeActive = true;
            param1.SetPhase(this.GoblinPhaseTick);
         }
      }
      
      public function GoblinPhaseTick(param1:a_GameHook) : void
      {
         if(param1.AtTime(0))
         {
            param1.PlayScript(this.Script_NicelyDone);
            param1.ShowTutorial("am_HighlighterHealthBar");
         }
         if(param1.AtTime(4850))
         {
            param1.HideTutorial("am_HighlighterHealthBar");
            param1.PlayScript(this.Script_BeAlert);
         }
         if(param1.OnScriptFinish(this.Script_BeAlert))
         {
            this.am_Goblin0.Remove();
            this.am_Goblin1.Remove();
            this.am_Goblin2.Remove();
            this.am_GStub1.Remove();
            this.am_GStub2.Remove();
            this.am_GStub3.Remove();
            this.am_GStub4.Remove();
            this.am_GStub5.Remove();
            param1.ShowTutorial("am_HighlighterMelee");
            param1.PlayScript(this.Script_OverlayDelay2);
         }
         if(param1.OnScriptFinish(this.Script_OverlayDelay2))
         {
            this.am_Goblin3.Spawn();
         }
         if(this.am_Goblin3.OnDefeat())
         {
            param1.HideTutorial("am_HighlighterMelee");
            param1.PlayScript(this.Script_GoblinWait);
         }
         if(param1.OnScriptFinish(this.Script_GoblinWait))
         {
            this.am_Goblin4.Spawn();
            this.am_Goblin5.Spawn();
            this.am_Goblin6.Spawn();
            this.bWaveTwoActive = true;
         }
         if(this.bWaveTwoActive && this.am_Goblin4.Defeated() && this.am_Goblin5.Defeated() && this.am_Goblin6.Defeated())
         {
            this.bWaveTwoActive = false;
            param1.PlayScript(this.Script_GoblinWait2);
         }
         if(param1.OnScriptFinish(this.Script_GoblinWait2))
         {
            this.am_Goblin7.Spawn();
            this.am_Goblin8.Spawn();
            this.am_Goblin9.Spawn();
            this.bWaveThreeActive = true;
         }
         if(this.bWaveThreeActive && this.am_Goblin7.Defeated() && this.am_Goblin8.Defeated() && this.am_Goblin9.Defeated())
         {
            this.bWaveThreeActive = false;
            param1.PlayScript(this.Script_LooksLikeWeAreInTheClear);
            param1.SetPhase(this.KrakenPhaseTick);
         }
      }
      
      public function KrakenPhaseTick(param1:a_GameHook) : void
      {
         if(param1.OnScriptFinish(this.Script_LooksLikeWeAreInTheClear))
         {
            this.am_Boss.Spawn();
            this.am_LastMonster.Remove();
            param1.bossFightPhase = this.BossTick;
         }
      }
      
      public function BossTick(param1:a_GameHook) : void
      {
         if(param1.AtTime(0))
         {
            param1.Animate("am_KrakenBody","Rise",false);
            param1.Animate("am_TBack","Rise",false);
            param1.Animate("am_TFrontLeft","Rise",false);
            param1.Animate("am_Hump1","Rise",false);
            param1.Animate("am_Hump2","Rise",false);
         }
         if(param1.AtTime(600))
         {
            param1.PlaySound("NPC_Boss_Kraken_Smash",2);
         }
         var _loc2_:Boolean = false;
         if(this.am_Boss.AtHealth(0.9))
         {
            _loc2_ = true;
         }
         else if(this.am_Boss.AtHealth(0.8))
         {
            _loc2_ = true;
         }
         else if(this.am_Boss.AtHealth(0.7))
         {
            _loc2_ = true;
         }
         else if(this.am_Boss.AtHealth(0.6))
         {
            _loc2_ = true;
         }
         else if(this.am_Boss.AtHealth(0.5))
         {
            _loc2_ = true;
         }
         else if(this.am_Boss.AtHealth(0.4))
         {
            _loc2_ = true;
         }
         else if(this.am_Boss.AtHealth(0.3))
         {
            _loc2_ = true;
         }
         else if(this.am_Boss.AtHealth(0.2))
         {
            _loc2_ = true;
         }
         else if(this.am_Boss.AtHealth(0.1))
         {
            _loc2_ = true;
         }
         if(_loc2_)
         {
            param1.Animate("am_KrakenBody","HitReact",false);
            param1.PlaySound("SND_NPC_DevourerBig_Activate_01",3);
         }
         if(this.am_Boss.Defeated())
         {
            param1.Animate("am_KrakenBody","KO",true);
            param1.Animate("am_TBack","KO",true);
            param1.Animate("am_TFrontLeft","KO",true);
            param1.Animate("am_Hump1","KO",true);
            param1.Animate("am_Hump2","KO",true);
            param1.SetPhase(this.CloseLevelTick);
         }
      }
      
      public function CloseLevelTick(param1:a_GameHook) : void
      {
         if(param1.AtTime(25000))
         {
            param1.ShowTutorial("am_WhiteOut");
            param1.SetPhase(null);
         }
      }
      
      internal function __setProp_am_Parrot_a_Room_TutorialBoat_R01_cue_0() : *
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
      
      internal function __setProp_am_Goblin3_a_Room_TutorialBoat_R01_cue_0() : *
      {
         try
         {
            this.am_Goblin3["componentInspectorSetting"] = true;
         }
         catch(e:Error)
         {
         }
         this.am_Goblin3.characterName = "";
         this.am_Goblin3.displayName = "";
         this.am_Goblin3.dramaAnim = "";
         this.am_Goblin3.itemDrop = "";
         this.am_Goblin3.sayOnActivate = "Mwahahaha!";
         this.am_Goblin3.sayOnAlert = "";
         this.am_Goblin3.sayOnBloodied = "";
         this.am_Goblin3.sayOnDeath = "";
         this.am_Goblin3.sayOnInteract = "";
         this.am_Goblin3.sayOnSpawn = "";
         this.am_Goblin3.sleepAnim = "";
         this.am_Goblin3.team = "default";
         this.am_Goblin3.waitToAggro = 0;
         try
         {
            this.am_Goblin3["componentInspectorSetting"] = false;
         }
         catch(e:Error)
         {
         }
      }
      
      internal function __setProp_am_Goblin6_a_Room_TutorialBoat_R01_cue_0() : *
      {
         try
         {
            this.am_Goblin6["componentInspectorSetting"] = true;
         }
         catch(e:Error)
         {
         }
         this.am_Goblin6.characterName = "";
         this.am_Goblin6.displayName = "";
         this.am_Goblin6.dramaAnim = "";
         this.am_Goblin6.itemDrop = "";
         this.am_Goblin6.sayOnActivate = "";
         this.am_Goblin6.sayOnAlert = "";
         this.am_Goblin6.sayOnBloodied = "";
         this.am_Goblin6.sayOnDeath = "No fair!";
         this.am_Goblin6.sayOnInteract = "";
         this.am_Goblin6.sayOnSpawn = "";
         this.am_Goblin6.sleepAnim = "";
         this.am_Goblin6.team = "default";
         this.am_Goblin6.waitToAggro = 0;
         try
         {
            this.am_Goblin6["componentInspectorSetting"] = false;
         }
         catch(e:Error)
         {
         }
      }
      
      internal function __setProp_am_Goblin4_a_Room_TutorialBoat_R01_cue_0() : *
      {
         try
         {
            this.am_Goblin4["componentInspectorSetting"] = true;
         }
         catch(e:Error)
         {
         }
         this.am_Goblin4.characterName = "";
         this.am_Goblin4.displayName = "";
         this.am_Goblin4.dramaAnim = "";
         this.am_Goblin4.itemDrop = "";
         this.am_Goblin4.sayOnActivate = "Tehehe";
         this.am_Goblin4.sayOnAlert = "";
         this.am_Goblin4.sayOnBloodied = "";
         this.am_Goblin4.sayOnDeath = "@Back to the deep with you, trog scum!";
         this.am_Goblin4.sayOnInteract = "";
         this.am_Goblin4.sayOnSpawn = "";
         this.am_Goblin4.sleepAnim = "";
         this.am_Goblin4.team = "default";
         this.am_Goblin4.waitToAggro = 0;
         try
         {
            this.am_Goblin4["componentInspectorSetting"] = false;
         }
         catch(e:Error)
         {
         }
      }
      
      internal function __setProp_am_Goblin7_a_Room_TutorialBoat_R01_cue_0() : *
      {
         try
         {
            this.am_Goblin7["componentInspectorSetting"] = true;
         }
         catch(e:Error)
         {
         }
         this.am_Goblin7.characterName = "";
         this.am_Goblin7.displayName = "";
         this.am_Goblin7.dramaAnim = "";
         this.am_Goblin7.itemDrop = "";
         this.am_Goblin7.sayOnActivate = "These seas are ours!";
         this.am_Goblin7.sayOnAlert = "";
         this.am_Goblin7.sayOnBloodied = "";
         this.am_Goblin7.sayOnDeath = "";
         this.am_Goblin7.sayOnInteract = "";
         this.am_Goblin7.sayOnSpawn = "";
         this.am_Goblin7.sleepAnim = "";
         this.am_Goblin7.team = "default";
         this.am_Goblin7.waitToAggro = 0;
         try
         {
            this.am_Goblin7["componentInspectorSetting"] = false;
         }
         catch(e:Error)
         {
         }
      }
      
      internal function __setProp_am_Goblin8_a_Room_TutorialBoat_R01_cue_0() : *
      {
         try
         {
            this.am_Goblin8["componentInspectorSetting"] = true;
         }
         catch(e:Error)
         {
         }
         this.am_Goblin8.characterName = "";
         this.am_Goblin8.displayName = "";
         this.am_Goblin8.dramaAnim = "";
         this.am_Goblin8.itemDrop = "";
         this.am_Goblin8.sayOnActivate = "This ship is going down!";
         this.am_Goblin8.sayOnAlert = "";
         this.am_Goblin8.sayOnBloodied = "";
         this.am_Goblin8.sayOnDeath = "";
         this.am_Goblin8.sayOnInteract = "";
         this.am_Goblin8.sayOnSpawn = "";
         this.am_Goblin8.sleepAnim = "";
         this.am_Goblin8.team = "default";
         this.am_Goblin8.waitToAggro = 0;
         try
         {
            this.am_Goblin8["componentInspectorSetting"] = false;
         }
         catch(e:Error)
         {
         }
      }
      
      internal function __setProp_am_Boss_a_Room_TutorialBoat_R01_cue_0() : *
      {
         try
         {
            this.am_Boss["componentInspectorSetting"] = true;
         }
         catch(e:Error)
         {
         }
         this.am_Boss.characterName = "IntroKraken";
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
      
      internal function __setProp_am_Fink_a_Room_TutorialBoat_R01_cue_0() : *
      {
         try
         {
            this.am_Fink["componentInspectorSetting"] = true;
         }
         catch(e:Error)
         {
         }
         this.am_Fink.characterName = "";
         this.am_Fink.displayName = "";
         this.am_Fink.dramaAnim = "";
         this.am_Fink.itemDrop = "";
         this.am_Fink.sayOnActivate = "";
         this.am_Fink.sayOnAlert = "";
         this.am_Fink.sayOnBloodied = "";
         this.am_Fink.sayOnDeath = "";
         this.am_Fink.sayOnInteract = "";
         this.am_Fink.sayOnSpawn = "";
         this.am_Fink.sleepAnim = "";
         this.am_Fink.team = "neutral";
         this.am_Fink.waitToAggro = 0;
         try
         {
            this.am_Fink["componentInspectorSetting"] = false;
         }
         catch(e:Error)
         {
         }
      }
      
      internal function frame1() : *
      {
         this.Script_BeAlert = ["5 Player Be alert, Death Eyes mean goblins aren\'t far away.","12 Parrot <Scared>Kraken Raiders! Off the bow!","8 Player Hold her steady, Captain. I\'ll repel all boarders!","8 Camera 1","4 Goblin1 <PullLever>Humans! What are humans doing here!?!","1 Goblin0 <Cheer>","0 Sound a_Sound_GoblinGrunt 3.0","4 Goblin2 <Cheer>Sink them! We can\'t be followed!","0 GStub4 <Cheer>","0 Sound a_Sound_GoblinGrunt2 4.0","1 Goblin0 <Cheer>","0 Sound a_Sound_GoblinGrunt2 3.0","0 GStub2 <Cheer>","1 GStub3 <Cheer>","0 Sound a_Sound_GoblinGrunt 3.0","0 GStub4 <Cheer>","1 GStub1 <Cheer>","0 Sound a_Sound_GoblinGrunt2 4.0","1 GStub5 <Cheer>","4 Goblin1 <PullLever>CHARGE!","0 Sound a_Sound_GoblinGrunt 6.0","0 Sound a_Sound_GoblinRumble 3.0","3 Goblin1 <Goto Red 3>","1 Goblin0 <Goto Red 3>","0 Sound a_Sound_GoblinGrunt 3.0","1 Goblin2 <Goto Red 3>","0 GStub1 <Goto Red 3>","1 GStub2 <Goto Red 3>","0 Sound a_Sound_GoblinGrunt2 4.0","0 GStub3 <Goto Red 3>","1 GStub4 <Goto Red 3>","0 Sound a_Sound_GoblinRumble 4.0"
         ,"1 GStub5 <Goto Red 3>","6 Camera 2","2 Parrot <Goto Red 4>","3 Parrot <Panic>Boarders!","2 End"];
         this.Script_OverlayDelay = ["8 End"];
         this.Script_OverlayDelay2 = ["13 End"];
         this.Script_TheStorm = ["12 Player Steady, Captain. We\'ll weather this storm.","12 Fink It\'s not the storm I fear.","12 Fink No ship has sailed these waters since the Goblin Monster Fleets appeared.","16 Player True, but the Goblin Horde is defeated. The war is over.","14 Fink Aye, back home, but we\'re far from home.","12 End"];
         this.Script_LookOutFliers = ["0 Parrot <Goto Red 1>","8 Parrot <Scared>Goblin Death Eyes! From the East!","3 End"];
         this.Script_LooksLikeWeAreInTheClear = ["0 Boss <Goto Red 8>","6 Fink Nasty Trogs!","4 Parrot <Panic>The rest are fleeing towards the coast...","1 Parrot <Panic>"];
         this.Script_GoblinWait = ["2 Parrot <Panic>Here come more!","4 End"];
         this.Script_Shootem = ["0 Parrot <Panic>Shoot\'em down!"];
         this.Script_NicelyDone = ["2 Parrot Nicely Done!"];
         this.Script_VileSeaDemons = ["4 Fink Wretched things!"];
         this.Script_LookOut = ["2 Parrot <Panic>Incoming!"];
         this.Script_GoblinWait2 = ["4 End"];
         this.bTutorialVisible = false;
         this.bWaveTwoActive = false;
         this.bWaveThreeActive = false;
         this.bWaveFourActive = false;
      }
   }
}

