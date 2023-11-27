import os
import random
import math
import pygame
from os import listdir
from os.path import isfile, join # dynamic loading
pygame.init() # initialise pygame module

pygame.display.set_caption("Platformer")

WIDTH, HEIGHT = 1000,800
FPS = 60
PLAYER_VEL = 5

# windows need dimension
window = pygame.display.set_mode((WIDTH,HEIGHT))

def flip(sprites):
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites] # flip horizontally or vertically

def load_sprite_sheets(dir1, dir2, width, height, direction=False):
    path = join("assets", dir1, dir2)
    images = [f for f in listdir(path) if isfile(join(path,f))] #load all the files inside the dir

    all_sprites = {}

    for image in images:
        sprite_sheet = pygame.image.load(join(path,image)).convert_alpha() #load a transparent bg image

        sprites = []
        for i in range(sprite_sheet.get_width() // width): ## check
            surface = pygame.Surface((width, height), pygame.SRCALPHA,32) #pygame function
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(sprite_sheet, (0,0), rect) #blit kinda means draw
            sprites.append(pygame.transform.scale2x(surface))

        #replace the images and seperate to left and right
        if direction:
            all_sprites[image.replace(".png", "") + "_right"] = sprites
            all_sprites[image.replace(".png", "") + "_left"] = flip(sprites)
        else:
            all_sprites[image.replace(".png", "")] = sprites

    return all_sprites

def get_block(size): #size is the size of the block
    path = join("assets", "terrain", "Terrain.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((size,size), pygame.SRCALPHA, 32)
    # adjust the x axis to load the image
    rect = pygame.Rect(96, 0, size, size) #taking the block that is 96 pixel in the image which is the 2nd block in the image
    surface.blit(image, (0,0), rect)

    return pygame.transform.scale2x(surface) #optional scale

class Player(pygame.sprite.Sprite): #Player class
    # super().__init__()
    COLOR = (255, 0, 0)
    GRAVITY = 1
    SPRITES = load_sprite_sheets("MainCharacters", "MaskDude", 32, 32, True)
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height) #rect in this case is a tuple that store 4 individual value
        self.x_vel = 0
        self.y_vel = 0
        self.mask = None
        self.direction = "left"
        self.animation_count = 0
        self.fall_count = 0 # how long in the air
        self.jump_count = 0 # for jumping
        self.hit = False
        self.hit_count = 0

    def jump(self):
        self.y_vel = -self.GRAVITY * 8 # negative cause jump up
        self.animation_count = 0
        self.jump_count += 1
        if self.jump_count == 1:
            self.fall_count = 0

    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

    def make_hit(self):
        self.hit = True
        self.hit_count = 0

    def move_left(self,vel):
        self.x_vel = -vel
        if self.direction != "left":
            self.direction = "left"
            self.animation_count = 0

    def move_right(self,vel):
        self.x_vel = vel
        if self.direction != "right":
            self.direction = "right"
            self.animation_count = 0

    def loop(self, fps): # call once every frame
        self.y_vel += min(1, (self.fall_count / fps) * self.GRAVITY) #fall_count/fps = seconds = gravity
        self.move(self.x_vel, self.y_vel)

        if self.hit:
            self.hit_count += 1
        if self.hit_count > fps * 2:
            self.hit = False
            self.hit_count = 0

        self.fall_count += 1
        self.update_sprite() #update the sprite for every single frame

    def landed(self):
        self.fall_count = 0
        self.y_vel = 0
        self.jump_count = 0

    def hit_head(self):
        self.count = 0
        self.y_vel *= -1    

    def update_sprite(self):
        sprite_sheet = "idle"
        if self.hit:
            sprite_sheet = "hit"
        if self.y_vel != 0:
            if self.jump_count == 1:
                sprite_sheet = "jump"
            elif self.jump_count == 2:
                sprite_sheet = "double_jump"
        elif self.y_vel > self.GRAVITY * 2: # falling
            sprite_sheet = "fall"
        elif self.x_vel != 0:
            sprite_sheet = "run"

        sprite_sheet_name = sprite_sheet + "_" + self.direction
        sprites = self.SPRITES[sprite_sheet_name] # iterate the sprites and changing the sprites
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.sprite = sprites[sprite_index]
        self.animation_count += 1
        self.update()

    def update(self):
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y)) # the rect is constantly adjusted
        self.mask = pygame.mask.from_surface(self.sprite) #pixels colliding instead of rectangle, the mask solves the problem

    def draw(self, win, offset_x):
        # self.sprite = self.SPRITES["idle_" + self.direction][0]
        win.blit(self.sprite, (self.rect.x - offset_x, self.rect.y))

class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, name=None):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.width = width
        self.height = height
        self.name = name
    
    def draw(self, win, offset_x):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y))

class Block(Object):
    def __init__(self, x, y, size) :
        super().__init__(x, y, size, size)
        block = get_block(size)
        self.image.blit(block, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)

class Fire(Object):
    ANIMATION_DELAY = 3

    def __init__(self, x, y ,width, height):
        super().__init__(x, y, width, height, "fire")
        self.fire = load_sprite_sheets("Traps", "fire", width, height)
        self.image = self.fire["off"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "off"

    def on(self):
        self.animation_name = "on"

    def off(self):
        self.animation_name = "off"

    def loop(self):
        sprites = self.fire[self.animation_name] # iterate the sprites and changing the sprites
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1
        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y)) 
        self.mask = pygame.mask.from_surface(self.image)

        if self.animation_count // self.ANIMATION_DELAY > len(sprites):
            self.animation_count = 0

def get_background(name): #name of background
    image = pygame.image.load(join("assets", "Background", name)) #join means call on directory
    # x,y,width,height
    _, _, width, height = image.get_rect() # _ means no cares on value
    tiles = []

    for i in range(WIDTH // width + 1): # +1 is to make is to make sure no gaps 
        for j in range(HEIGHT // height + 1):
            pos = (i * width, j * height)
            tiles.append(pos)

    return tiles, image

# draw the image from the top left window
def draw(window, background, bg_image, player, objects, offset_x):
    for tile in background:
        window.blit(bg_image, tile) #fill the tile with the bg_image

    for obj in objects:
        obj.draw(window, offset_x)

    player.draw(window, offset_x)

    pygame.display.update() # Need to update everytime draw something so it refreshes

def handle_vertical_collison(player, objects, dy):
    collided_objects = []
    for obj in objects:
        if pygame.sprite.collide_mask(player,obj): #object inhereted from the sprite class
            if dy > 0: # if down and collide top of object
                player.rect.bottom = obj.rect.top
                player.landed()
            elif dy < 0:
                player.rect.top = obj.rect.bottom
                player.hit_head()

            collided_objects.append(obj)
    
    return collided_objects

def collide(player, objects, dx):
    player.move(dx, 0) #horizontal velocity
    player.update() # update rect and mask before check for coliision
    collided_object = None
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            collided_object = obj
            break
    
    player.move(-dx,0) #move back
    player.update
    
    return collided_object

def handle_move(player, objects):
    keys = pygame.key.get_pressed()

    player.x_vel = 0
    collide_left = collide(player, objects, -PLAYER_VEL * 2)
    collide_right = collide(player, objects, PLAYER_VEL * 2)


    if keys[pygame.K_a] and not collide_left:
        player.move_left(PLAYER_VEL)
    if keys[pygame.K_d] and not collide_right:
        player.move_right(PLAYER_VEL)

    vertical_collide = handle_vertical_collison(player, objects, player.y_vel)
    to_check = [collide_left , collide_right, *vertical_collide]
    for obj in to_check:
        if obj and obj.name == "fire":
            player.make_hit()

def main(window):
    clock = pygame.time.Clock()
    background, bg_image = get_background("Blue.png")

    block_size = 96

    player = Player(100, 100, 50, 50)
    fire = Fire(100, HEIGHT - block_size - 64, 16, 32)
    fire.on()
    floor = [Block(i * block_size, HEIGHT - block_size, block_size) for i in range(-WIDTH // block_size, WIDTH * 2 // block_size)] # fillup the block to the left and right of the screen
    # blocks = [Block(0, HEIGHT - block_size, block_size)]

    objects = [*floor, Block(0, HEIGHT - block_size * 2, block_size), Block(block_size * 3, HEIGHT - block_size * 4, block_size), fire]

    # for self scrolling
    offset_x = 0
    scroll_area_width = 200

    run = True
    while run: # this means run is True
        clock.tick(FPS)

        # key = pygame.key.get_pressed()

        # this is event handler
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break

            if event.type == pygame.KEYDOWN: # inserted in event queue when the keys are pressed and released
                if event.key == pygame.K_SPACE and player.jump_count < 2:
                    player.jump()
        
        player.loop(FPS)
        fire.loop()
        handle_move(player, objects)
        draw(window, background, bg_image, player, objects, offset_x)

        if (player.rect.right - offset_x >= WIDTH - scroll_area_width and player.x_vel > 0) or (player.rect.left - offset_x <= scroll_area_width and player.x_vel < 0):
            offset_x += player.x_vel
    
    pygame.quit()
    quit()

# ONLY CALL MAIN FUNCTION IF WE RUN THIS FILE DIRECTLY
if __name__ == "__main__":
    main(window)

# WINDOW > GAME LOOP > EVENT HANDLER

# if hit go back 