package com.mojang.rubydung;

import com.mojang.rubydung.level.Level;
import com.mojang.rubydung.phys.AABB;
import java.util.List;
import org.lwjgl.input.Keyboard;

public class Player {
   private Level level;
   public float xo;
   public float yo;
   public float zo;
   public float x;
   public float y;
   public float z;
   public float xd;
   public float yd;
   public float zd;
   public float yRot;
   public float xRot;
   public AABB bb;
   public boolean onGround = false;
   public boolean flight = false; 

   public Player(Level level) {
      this.level = level;
      this.resetPos();
   }

   private void resetPos() {
      float x = (float)Math.random() * this.level.width;
      float y = this.level.depth + 10;
      float z = (float)Math.random() * this.level.height;
      this.setPos(x, y, z);
   }

   private void setPos(float x, float y, float z) {
      this.x = x;
      this.y = y;
      this.z = z;
      float w = 0.3F;
      float h = 0.9F;
      this.bb = new AABB(x - w, y - h, z - w, x + w, y + h, z + w);
   }

   public void turn(float xo, float yo) {
      this.yRot = (float)(this.yRot + xo * 0.15);
      this.xRot = (float)(this.xRot - yo * 0.15);
      if (this.xRot < -90.0F) {
         this.xRot = -90.0F;
      }

      if (this.xRot > 90.0F) {
         this.xRot = 90.0F;
      }
   }

   public void tick() {
      this.xo = this.x;
      this.yo = this.y;
      this.zo = this.z;
      float xa = 0.0F;
      float ya = 0.0F;
      if (Keyboard.isKeyDown(19)) {
         this.resetPos();
      }

      if (Keyboard.isKeyDown(200) || Keyboard.isKeyDown(17)) {
         ya--;
      }

      if (Keyboard.isKeyDown(208) || Keyboard.isKeyDown(31)) {
         ya++;
      }

      if (Keyboard.isKeyDown(203) || Keyboard.isKeyDown(30)) {
         xa--;
      }

      if (Keyboard.isKeyDown(205) || Keyboard.isKeyDown(32)) {
         xa++;
      }

      if ((Keyboard.isKeyDown(57) || Keyboard.isKeyDown(219)) && this.onGround) {
         this.yd = 0.12F;
      }

      // Toggle flight (T)
      if (Keyboard.isKeyDown(20)) this.flight = !this.flight;

      // Vertical controls (Space / Shift)
      if (Keyboard.isKeyDown(57) || Keyboard.isKeyDown(219)) {
         if (this.onGround)   this.yd = 0.12F;  // Jump
         else if (this.flight) this.yd = 0.03F;  // Fly up
      }
      if (Keyboard.isKeyDown(42) && this.flight) this.yd = -0.01F; // Fly down

      float speed = this.flight ? 0.03F : this.onGround ? 0.02F : 0.005F;
      this.moveRelative(xa, ya, speed);
      if (!this.flight) this.yd -= 0.005F;
      this.move(this.xd, this.yd, this.zd);
      if (this.flight) {
	        this.xd *= 0.75F;
	        this.yd *= 0.75F;
	        this.zd *= 0.75F;
	    } else {
	        this.xd *= 0.91F;
	        this.yd *= 0.98F;
	        this.zd *= 0.91F;
	        if (this.onGround) {
	            this.xd *= 0.8F;
	            this.zd *= 0.8F;
	        }
	    }
   }

   public void move(float xa, float ya, float za) {
      float xaOrg = xa;
      float yaOrg = ya;
      float zaOrg = za;
      List<AABB> aABBs = this.level.getCubes(this.bb.expand(xa, ya, za));

      for (int i = 0; i < aABBs.size(); i++) {
         ya = aABBs.get(i).clipYCollide(this.bb, ya);
      }

      this.bb.move(0.0F, ya, 0.0F);

      for (int i = 0; i < aABBs.size(); i++) {
         xa = aABBs.get(i).clipXCollide(this.bb, xa);
      }

      this.bb.move(xa, 0.0F, 0.0F);

      for (int i = 0; i < aABBs.size(); i++) {
         za = aABBs.get(i).clipZCollide(this.bb, za);
      }

      this.bb.move(0.0F, 0.0F, za);
      this.onGround = yaOrg != ya && yaOrg < 0.0F;
      if (xaOrg != xa) {
         this.xd = 0.0F;
      }

      if (yaOrg != ya) {
         this.yd = 0.0F;
      }

      if (zaOrg != za) {
         this.zd = 0.0F;
      }

      this.x = (this.bb.x0 + this.bb.x1) / 2.0F;
      this.y = this.bb.y0 + 1.62F;
      this.z = (this.bb.z0 + this.bb.z1) / 2.0F;
   }

   public void moveRelative(float xa, float za, float speed) {
      float dist = xa * xa + za * za;
      if (!(dist < 0.01F)) {
         dist = speed / (float)Math.sqrt(dist);
         xa *= dist;
         za *= dist;
         float sin = (float)Math.sin(this.yRot * Math.PI / 180.0);
         float cos = (float)Math.cos(this.yRot * Math.PI / 180.0);
         this.xd += xa * cos - za * sin;
         this.zd += za * cos + xa * sin;
      }
   }
}
