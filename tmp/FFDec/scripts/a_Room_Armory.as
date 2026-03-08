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
   
   [Embed(source="/_assets/assets.swf", symbol="symbol2556")]
   public dynamic class a_Room_Armory extends MovieClip
   {
      public var am_RackRogueArmor:MovieClip;
      
      public var __id17_:ac_NPCHomeRunecrafter;
      
      public var am_RackRogueHat:MovieClip;
      
      public var am_RackRogueBoots:MovieClip;
      
      public var am_CollisionObject:MovieClip;
      
      public var am_RackPaladinArmor:MovieClip;
      
      public var am_RackPaladinShield:MovieClip;
      
      public var am_RackRogueSword:MovieClip;
      
      public var am_RackRogueGloves:MovieClip;
      
      public var am_RackMageArmor:MovieClip;
      
      public var am_RackMageGloves:MovieClip;
      
      public var am_RackMageSword:MovieClip;
      
      public var am_RackPaladinHat:MovieClip;
      
      public var am_RackRogueShield:MovieClip;
      
      public var am_RackMageShield:MovieClip;
      
      public var am_RackPaladinBoots:MovieClip;
      
      public var am_RackPaladinSword:MovieClip;
      
      public var am_RackMageBoots:MovieClip;
      
      public var am_RackMageHat:MovieClip;
      
      public var am_Foreground:MovieClip;
      
      public var am_RackPaladinGloves:MovieClip;
      
      public var __id18_:ac_SpyPaladinBoss;
      
      public var __id19_:ac_RockHulkBoss;
      
      public var __id20_:ac_GoblinKrakenBoss;
      
      public var __id21_:ac_SpyPaladinBoss;
      
      public var __id22_:ac_SpyRogueBoss;
      
      public var __id23_:ac_GhostBoss;
      
      public var __id24_:ac_GlowingSkeletonBoss;
      
      public var __id25_:ac_GreatPumpkin;
      
      public var __id26_:ac_AncientDragonGoldMini;
      
      public function a_Room_Armory()
      {
         super();
         this.__setProp___id17__a_Room_Armory_Cues_0();
         addChild(this.__id17_);
         this.__id19_ = new ac_RockHulkBoss();
         this.__id19_.x = 600;
         this.__id19_.y = 600;
         addChild(this.__id19_);
         this.__id20_ = new ac_GoblinKrakenBoss();
         this.__id20_.x = 700;
         this.__id20_.y = 600;
         addChild(this.__id20_);
         this.__id21_ = new ac_SpyPaladinBoss();
         this.__id21_.x = 800;
         this.__id21_.y = 600;
         addChild(this.__id21_);
         this.__id22_ = new ac_SpyRogueBoss();
         this.__id22_.x = 900;
         this.__id22_.y = 600;
         addChild(this.__id22_);
         this.__id23_ = new ac_GhostBoss();
         this.__id23_.x = 1000;
         this.__id23_.y = 600;
         addChild(this.__id23_);
         this.__id24_ = new ac_GlowingSkeletonBoss();
         this.__id24_.x = 1200;
         this.__id24_.y = 600;
         addChild(this.__id24_);
         this.__id25_ = new ac_GreatPumpkin();
         this.__id25_.x = 1300;
         this.__id25_.y = 600;
         addChild(this.__id25_);
         this.__id26_ = new ac_AncientDragonGoldMini();
         this.__id26_.x = 1300;
         this.__id26_.y = 600;
         addChild(this.__id26_);
      }
      
      internal function __setProp___id17__a_Room_Armory_Cues_0() : *
      {
         try
         {
            this.__id17_["componentInspectorSetting"] = true;
         }
         catch(e:Error)
         {
         }
         this.__id17_.characterName = "Special_Runecrafter";
         this.__id17_.displayName = "Hidden";
         this.__id17_.dramaAnim = "";
         this.__id17_.itemDrop = "";
         this.__id17_.sayOnActivate = "";
         this.__id17_.sayOnAlert = "";
         this.__id17_.sayOnBloodied = "";
         this.__id17_.sayOnDeath = "";
         this.__id17_.sayOnInteract = "I\'ll keep this gear polished up.";
         this.__id17_.sayOnSpawn = "";
         this.__id17_.sleepAnim = "";
         this.__id17_.team = "neutral";
         this.__id17_.waitToAggro = 0;
         try
         {
            this.__id17_["componentInspectorSetting"] = false;
         }
         catch(e:Error)
         {
         }
      }
   }
}

