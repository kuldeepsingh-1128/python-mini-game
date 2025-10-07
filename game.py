import pygame
import os
import random
import sys
import math
import numpy as np

pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)


SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600
FPS = 60
PLAYER_SPEED = 5
JUMP_STRENGTH = -15
GRAVITY = 0.8
ENEMY_SPEED = 2

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)
CYAN = (0, 255, 255)
BROWN = (139, 69, 19)
GRAY = (128, 128, 128)
PINK = (255, 192, 203)
DARK_RED = (139, 0, 0)
LIME = (0, 255, 0)

def generate_beep(frequency, duration, volume=0.3):
    """Generate a simple beep sound"""
    try:
        frames = int(duration * 22050)
        arr = np.sin(2 * np.pi * frequency * np.linspace(0, duration, frames))
        arr = (arr * volume * 32767).astype(np.int16)
        arr = np.repeat(arr.reshape(frames, 1), 2, axis=1)
        return pygame.sndarray.make_sound(arr)
    except:
        return None

JUMP_SOUND = generate_beep(400, 0.2, 0.2)
COIN_SOUND = generate_beep(800, 0.3, 0.3)
POWERUP_SOUND = generate_beep(600, 0.4, 0.25)
HIT_SOUND = generate_beep(200, 0.5, 0.4)
ENGINE_SOUND = generate_beep(150, 0.1, 0.1)
SHOOT_SOUND = generate_beep(1500, 0.06, 0.15)
BLAST_SOUND = generate_beep(900, 0.18, 0.35)
DINO_JUMP_SOUND = generate_beep(1200, 0.06, 0.22)

def play_sound(sound):
    """Safely play a sound"""
    if sound:
        try:
            sound.play()
        except:
            pass

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 40
        self.height = 50
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = False
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.speed_boost_timer = 0
        self.invulnerable_timer = 0
        self.reverse_controls = 0
        self.big_jump_timer = 0

    def update(self, platforms):

        if self.speed_boost_timer > 0:
            self.speed_boost_timer -= 1
        if self.invulnerable_timer > 0:
            self.invulnerable_timer -= 1
        if self.reverse_controls > 0:
            self.reverse_controls -= 1
        if self.big_jump_timer > 0:
            self.big_jump_timer -= 1
            
        keys = pygame.key.get_pressed()
        self.vel_x = 0
        
        current_speed = PLAYER_SPEED * 2 if self.speed_boost_timer > 0 else PLAYER_SPEED
        jump_power = JUMP_STRENGTH * 1.5 if self.big_jump_timer > 0 else JUMP_STRENGTH
        

        if self.reverse_controls > 0:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.vel_x = current_speed
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.vel_x = -current_speed
        else:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.vel_x = -current_speed
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.vel_x = current_speed
                
        if (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]) and self.on_ground:
            self.vel_y = jump_power
            play_sound(JUMP_SOUND)
            

        self.vel_y += GRAVITY
        
        self.x += self.vel_x
        self.y += self.vel_y
    
        if self.x < 0:
            self.x = 0
        elif self.x > SCREEN_WIDTH - self.width:
            self.x = SCREEN_WIDTH - self.width
            

        self.rect.x = self.x
        self.rect.y = self.y
        

        self.on_ground = False
        for platform in platforms:
            if hasattr(platform, 'visible') and not platform.visible:
                continue
                
            if self.rect.colliderect(platform.rect):
                if self.vel_y > 0 and self.rect.bottom <= platform.rect.top + 20:
                    self.rect.bottom = platform.rect.top
                    self.y = self.rect.y
                    self.vel_y = 0
                    self.on_ground = True

                elif self.vel_y < 0 and self.rect.top >= platform.rect.bottom - 20:
                    self.rect.top = platform.rect.bottom
                    self.y = self.rect.y
                    self.vel_y = 0
        

        if self.y >= SCREEN_HEIGHT - 100 - self.height:
            self.y = SCREEN_HEIGHT - 100 - self.height
            self.vel_y = 0
            self.on_ground = True
            
    def draw(self, screen):

        player_color = RED
        if self.invulnerable_timer > 0:
            player_color = WHITE if (self.invulnerable_timer // 5) % 2 else RED
        elif self.speed_boost_timer > 0:
            player_color = ORANGE
        elif self.reverse_controls > 0:
            player_color = PURPLE
        elif self.big_jump_timer > 0:
            player_color = LIME
            
        pygame.draw.rect(screen, player_color, self.rect)

        pygame.draw.rect(screen, player_color, (self.x, self.y - 5, self.width, 10))

        pygame.draw.rect(screen, (255, 220, 177), (self.x + 5, self.y + 5, self.width - 10, 20))

class Platform:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        
    def update(self):
        pass
        
    def draw(self, screen):
        pygame.draw.rect(screen, BROWN, self.rect)
        pygame.draw.rect(screen, BLACK, self.rect, 2)

class MovingPlatform(Platform):
    def __init__(self, x, y, width, height, start_x, end_x, speed=1):
        super().__init__(x, y, width, height)
        self.start_x = start_x
        self.end_x = end_x
        self.speed = speed
        self.direction = 1
        
    def update(self):
        self.x += self.speed * self.direction
        if self.x <= self.start_x or self.x >= self.end_x:
            self.direction *= -1
        self.rect.x = self.x
        
    def draw(self, screen):
        pygame.draw.rect(screen, BLUE, self.rect)
        pygame.draw.rect(screen, BLACK, self.rect, 2)

class DisappearingPlatform(Platform):
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height)
        self.visible = True
        self.timer = 0
        self.touch_timer = 0
        
    def update(self):
        self.timer += 1
        if self.touch_timer > 0:
            self.touch_timer -= 1
            if self.touch_timer <= 0:
                self.visible = not self.visible
                
    def trigger_disappear(self):
        if self.visible:
            self.touch_timer = 60
            
    def draw(self, screen):
        if self.visible:
            color = GRAY if self.touch_timer > 0 else BROWN
            pygame.draw.rect(screen, color, self.rect)
            pygame.draw.rect(screen, BLACK, self.rect, 2)

class BouncePlatform(Platform):
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height)
        
    def draw(self, screen):
        pygame.draw.rect(screen, PINK, self.rect)
        pygame.draw.rect(screen, BLACK, self.rect, 2)

class Enemy:
    def __init__(self, x, y, platform_left, platform_right):
        self.x = x
        self.y = y
        self.width = 30
        self.height = 30
        self.speed = ENEMY_SPEED
        self.direction = 1
        self.platform_left = platform_left
        self.platform_right = platform_right
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        
    def update(self):
        self.x += self.speed * self.direction
        if self.x <= self.platform_left or self.x >= self.platform_right - self.width:
            self.direction *= -1
        self.rect.x = self.x
        
    def draw(self, screen):
        pygame.draw.rect(screen, GREEN, self.rect)
        pygame.draw.circle(screen, BLACK, (self.x + 8, self.y + 8), 3)
        pygame.draw.circle(screen, BLACK, (self.x + 22, self.y + 8), 3)

class Coin:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 20
        self.height = 20
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        
    def draw(self, screen):
        pygame.draw.circle(screen, YELLOW, (self.x + 10, self.y + 10), 10)
        pygame.draw.circle(screen, BLACK, (self.x + 10, self.y + 10), 10, 2)

class RedCoin:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 25
        self.height = 25
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.glow_timer = 0
        
    def update(self):
        self.glow_timer += 1
        
    def draw(self, screen):
        glow_size = 12 + int(3 * math.sin(self.glow_timer * 0.2))
        pygame.draw.circle(screen, RED, (self.x + 12, self.y + 12), glow_size)
        pygame.draw.circle(screen, DARK_RED, (self.x + 12, self.y + 12), glow_size, 3)
        pygame.draw.circle(screen, WHITE, (self.x + 12, self.y + 12), 4)


class GoldenCoin:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 26
        self.height = 26
        self.rect = pygame.Rect(int(self.x), int(self.y), self.width, self.height)
        self.pulse = 0

    def update(self):
        self.pulse += 1

    def draw(self, screen, camera_x=0):
        draw_x = int(self.x - camera_x)
        draw_y = int(self.y)
        size = 12 + int(2 * math.sin(self.pulse * 0.2))
        pygame.draw.circle(screen, (255, 215, 0), (draw_x + 13, draw_y + 13), size)
        pygame.draw.circle(screen, (200, 160, 0), (draw_x + 13, draw_y + 13), size, 2)
        pygame.draw.circle(screen, WHITE, (draw_x + 13, draw_y + 13), 4)

class PowerUp:
    def __init__(self, x, y, power_type):
        self.x = x
        self.y = y
        self.width = 25
        self.height = 25
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.type = power_type
        
    def draw(self, screen):
        colors = {
            'speed': ORANGE,
            'jump': LIME,
            'invulnerable': WHITE,
            'reverse': PURPLE
        }
        pygame.draw.rect(screen, colors[self.type], self.rect)
        pygame.draw.rect(screen, BLACK, self.rect, 2)


class Dino:
    def __init__(self):
        self.x = 80
        self.width = 40
        self.height = 40

        ground_top = SCREEN_HEIGHT - 60
        self.y = ground_top - self.height
        self.vel_y = 0
        self.on_ground = True
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

        self.run_anim = 0
        self.run_timer = 0

    def update(self):

        self.vel_y += 1
        self.y += self.vel_y
        ground_top = SCREEN_HEIGHT - 60

        if self.y >= ground_top - self.height:
            self.y = ground_top - self.height
            self.vel_y = 0
            self.on_ground = True

        if self.on_ground:
            self.run_timer += 1
            if self.run_timer > 6:
                self.run_timer = 0
                self.run_anim = (self.run_anim + 1) % 2
        self.rect.topleft = (self.x, self.y)

    def jump(self):
        if self.on_ground:
            self.vel_y = -15
            self.on_ground = False

    def draw(self, screen):

        head_radius = 6
        head_x = int(self.x + self.width * 0.75)
        head_y = int(self.y + 8)

        torso_rect = pygame.Rect(int(self.x + 8), int(self.y + 8), 12, 20)
        pygame.draw.rect(screen, (200, 30, 30), torso_rect)

        pygame.draw.circle(screen, (255, 220, 177), (head_x, head_y), head_radius)

        if self.run_anim == 0:

            pygame.draw.line(screen, BLACK, (int(self.x + 12), int(self.y + 28)), (int(self.x + 6), int(self.y + 38)), 3)
            pygame.draw.line(screen, BLACK, (int(self.x + 20), int(self.y + 28)), (int(self.x + 26), int(self.y + 38)), 3)

            pygame.draw.line(screen, BLACK, (int(self.x + 14), int(self.y + 14)), (int(self.x + 4), int(self.y + 20)), 3)
            pygame.draw.line(screen, BLACK, (int(self.x + 20), int(self.y + 14)), (int(self.x + 30), int(self.y + 10)), 3)
        else:

            pygame.draw.line(screen, BLACK, (int(self.x + 12), int(self.y + 28)), (int(self.x + 6), int(self.y + 18)), 3)
            pygame.draw.line(screen, BLACK, (int(self.x + 20), int(self.y + 28)), (int(self.x + 26), int(self.y + 18)), 3)

            pygame.draw.line(screen, BLACK, (int(self.x + 14), int(self.y + 14)), (int(self.x + 4), int(self.y + 10)), 3)
            pygame.draw.line(screen, BLACK, (int(self.x + 20), int(self.y + 14)), (int(self.x + 30), int(self.y + 20)), 3)


class Cactus:
    def __init__(self, x):
        self.x = x
        self.y = SCREEN_HEIGHT - 50
        self.width = random.choice([20, 25, 30])

        self.height = random.choice([40, 48, 56])
        self.rect = pygame.Rect(self.x, self.y - self.height + 10, self.width, self.height)

    def update(self, speed):
        self.x -= speed
        self.rect.x = self.x

    def draw(self, screen):
        pygame.draw.rect(screen, GREEN, self.rect)


def dinosaur_game_over(screen, score, game=None):
    
    font = pygame.font.Font(None, 48)
    small_font = pygame.font.Font(None, 28)


    title = font.render("GAME OVER", True, (200, 0, 0))
    score_line = small_font.render(f"Jump Score: {score}", True, (0, 0, 0))
    if game is not None:
        total_line = small_font.render(f"Total Score: {game.Total_score}", True, (0, 0, 0))
        top_line = small_font.render(f"Top: {game.high_score}", True, (0, 0, 0))
    else:
        total_line = None
        top_line = None

    prompt = small_font.render("Press R to play again or ESC to exit", True, (10, 10, 10))


    popup_w, popup_h = 560, 220
    popup = pygame.Surface((popup_w, popup_h), pygame.SRCALPHA)
    popup.fill((240, 240, 240, 230))
    pygame.draw.rect(popup, (0, 0, 0), popup.get_rect(), 2)


    popup.blit(title, (popup_w//2 - title.get_width()//2, 16))
    popup.blit(score_line, (30, 80))
    if total_line:
        popup.blit(total_line, (30, 110))
    if top_line:
        popup.blit(top_line, (30, 140))
    popup.blit(prompt, (30, 170))


    popup_x = SCREEN_WIDTH//2 - popup_w//2
    popup_y = SCREEN_HEIGHT//2 - popup_h//2
    screen.blit(popup, (popup_x, popup_y))
    pygame.display.flip()

    waiting = True
    choice = 'quit'
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                waiting = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:

                    if game is not None:
                        try:
                            game.request_restart_to_platformer = True
                        except Exception:
                            pass
                    print('[dinosaur_game_over] R pressed: requesting restart')
                    choice = 'restart'
                    waiting = False
                elif event.key == pygame.K_ESCAPE:
                    waiting = False


    print(f'[dinosaur_game_over] returning choice={choice}')
    return choice


def dinosaur_main(game=None):
   
    
    standalone = game is None
    if standalone:
        pygame.init()
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Dinosaur Runner")
        clock = pygame.time.Clock()
    else:

        screen = game.screen
        clock = game.clock

    dino = Dino()
    cactuses = []
    spawn_timer = 0
    speed = 6
    score = 0
    font = pygame.font.Font(None, 28)

    running = True
    prev_score = 0
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE or event.key == pygame.K_UP:
                    dino.jump()
                    play_sound(DINO_JUMP_SOUND)
                elif event.key == pygame.K_ESCAPE:
                    running = False


        dino.update()
        spawn_timer += 1
        if spawn_timer > 90:
            spawn_timer = 0
            cactuses.append(Cactus(SCREEN_WIDTH + random.randint(10, 200)))

        for c in cactuses[:]:
            c.update(speed)
            if c.x + c.width < 0:
                cactuses.remove(c)
                score += 10

                if game is not None:
                    try:
                        delta = int(score - prev_score)
                        if delta > 0:
                            game.Total_score += delta
                            prev_score = score

                            if game.Total_score > getattr(game, 'high_score', 0):
                                game.high_score = int(game.Total_score)
                                try:
                                    with open(game.highscore_path, 'w') as f:
                                        f.write(str(game.high_score))
                                except Exception:
                                    pass
                    except Exception:
                        pass


        for c in cactuses:
            if dino.rect.colliderect(c.rect):

                result = dinosaur_game_over(screen, score, game)

                return (score, True if result == 'restart' else False)


        screen.fill((135, 206, 235))
        pygame.draw.rect(screen, BROWN, (0, SCREEN_HEIGHT - 60, SCREEN_WIDTH, 60))
        dino.draw(screen)
        for c in cactuses:
            c.draw(screen)

        score_text = font.render(f"Score: {score}", True, BLACK)
        screen.blit(score_text, (10, 10))

        if game is not None:
            Total_disp = font.render(f"Total: {game.Total_score}", True, BLACK)
            high_disp = font.render(f"Top: {game.high_score}", True, BLACK)
            screen.blit(Total_disp, (10, 40))
            high_x = SCREEN_WIDTH // 2 - high_disp.get_width() // 2
            screen.blit(high_disp, (high_x, 10))

        pygame.display.flip()
        clock.tick(FPS)

    if standalone:
        pygame.quit()
        return (score, False)
    else:
        
        return (score, False)



class Car:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 60
        self.height = 30
        self.vel_x = 0
        self.vel_y = 0
        self.fuel = 100
        self.distance = 0
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.engine_sound_timer = 0
        self.camera_x = 0
        
    def update(self):
        keys = pygame.key.get_pressed()
        
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vel_x += 0.5
            self.fuel -= 0.08

            self.engine_sound_timer += 1
            if self.engine_sound_timer % 30 == 0:
                play_sound(ENGINE_SOUND)
        elif keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vel_x -= 0.3
        
        self.vel_x *= 0.98  
        self.vel_y += 0.5   
        

        if self.vel_x > 8:
            self.vel_x = 8
        elif self.vel_x < -8:
            self.vel_x = -8
            
        self.x += self.vel_x
        self.y += self.vel_y
        

        target_camera = self.x - SCREEN_WIDTH // 3
        self.camera_x += (target_camera - self.camera_x) * 0.1
        

        if self.x < 0:
            self.x = 0
            self.vel_x = 0
            

        road_y = SCREEN_HEIGHT - 150
        if self.y >= road_y - self.height:
            self.y = road_y - self.height
            self.vel_y = 0
            
        if self.vel_x > 0:
            self.distance += abs(self.vel_x) * 0.1
            
        self.rect.x = self.x
        self.rect.y = self.y
        
    def draw(self, screen, camera_x=0):

        draw_x = self.x - camera_x
        draw_y = self.y
        

        car_rect = pygame.Rect(draw_x, draw_y, self.width, self.height)
        pygame.draw.rect(screen, RED, car_rect)
        pygame.draw.rect(screen, BLACK, car_rect, 2)
        

        wheel1_pos = (int(draw_x + 15), int(draw_y + self.height))
        wheel2_pos = (int(draw_x + 45), int(draw_y + self.height))
        
        pygame.draw.circle(screen, BLACK, wheel1_pos, 8)
        pygame.draw.circle(screen, BLACK, wheel2_pos, 8)
        pygame.draw.circle(screen, GRAY, wheel1_pos, 6)
        pygame.draw.circle(screen, GRAY, wheel2_pos, 6)
        

        pygame.draw.circle(screen, (255, 220, 177), (int(draw_x + 30), int(draw_y + 10)), 8)
        

        if abs(self.vel_x) > 4:
            for i in range(3):
                line_x = draw_x - 20 - i * 8
                line_y = draw_y + 10 + i * 5
                if line_x > -30:
                    pygame.draw.line(screen, WHITE, (line_x, line_y), (line_x - 6, line_y), 2)

class ObstacleCar:
    """Simple obstacle car that moves left in world coordinates."""
    def __init__(self, x, y, speed):
        self.x = x
        self.y = y
        self.width = 60
        self.height = 30
        self.speed = speed
        self.rect = pygame.Rect(int(self.x), int(self.y), self.width, self.height)

    def update(self):

        self.x -= self.speed
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)

    def draw(self, screen, camera_x=0):
        draw_x = int(self.x - camera_x)
        draw_y = int(self.y)
        car_rect = pygame.Rect(draw_x, draw_y, self.width, self.height)
        pygame.draw.rect(screen, (80, 0, 0), car_rect)
        pygame.draw.rect(screen, BLACK, car_rect, 2)

class Bullet:

    def __init__(self, x, y, speed=12):
        self.x = x
        self.y = y
        self.width = 8
        self.height = 4
        self.speed = speed
        self.rect = pygame.Rect(int(self.x), int(self.y), self.width, self.height)

    def update(self):
        self.x += self.speed
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)

    def draw(self, screen, camera_x=0):
        draw_x = int(self.x - camera_x)
        draw_y = int(self.y)
        pygame.draw.rect(screen, YELLOW, (draw_x, draw_y, self.width, self.height))


class MuzzleFlash:
    def __init__(self, x, y, lifetime=6):
        self.x = x
        self.y = y
        self.timer = 0
        self.lifetime = lifetime

    def update(self):
        self.timer += 1

    def draw(self, screen, camera_x=0):
        draw_x = int(self.x - camera_x)
        draw_y = int(self.y)
        size = 6 + (self.lifetime - self.timer)
        pygame.draw.circle(screen, (255, 220, 100), (draw_x, draw_y), size)


class Explosion:
    def __init__(self, x, y, max_time=18):
        self.x = x
        self.y = y
        self.timer = 0
        self.max_time = max_time

    def update(self):
        self.timer += 1

    def draw(self, screen, camera_x=0):
        progress = self.timer / max(1, self.max_time)
        radius = int(8 + progress * 48)
        alpha = int(max(0, 220 * (1 - progress)))
        surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        color_rgb = (255, int(max(0, 120 * (1 - progress))), 0)

        pygame.draw.circle(surf, color_rgb, (radius, radius), radius)
        surf.set_alpha(alpha)
        draw_x = int(self.x - camera_x) - radius
        draw_y = int(self.y) - radius
        screen.blit(surf, (draw_x, draw_y))

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("🔥 DevilCoder - Kuldeep singh 🔥")
        self.clock = pygame.time.Clock()
        self.running = True
        self.score = 0

        self.Total_score = 0

        self.last_score_snapshot = 0

        self.highscore_path = os.path.join(os.path.dirname(__file__), 'highscore.txt')
        self.high_score = 0
        try:
            if os.path.exists(self.highscore_path):
                with open(self.highscore_path, 'r') as f:
                    self.high_score = int(f.read().strip() or 0)
        except Exception:
            self.high_score = 0
        self.lives = 3
        self.font = pygame.font.Font(None, 36)
        self.chaos_timer = 0
        self.game_mode = "platformer"
        

        self.player = Player(50, SCREEN_HEIGHT - 200)
        

        self.car = Car(100, SCREEN_HEIGHT - 180)

        self.obstacles = []
        self.obstacle_timer = 0

        self.bullets = []
        self.bullet_cooldown = 0


        self.muzzles = []
        self.explosions = []

        self.golden_coin = None
        

        self.platforms = [
            Platform(0, SCREEN_HEIGHT - 100, SCREEN_WIDTH, 100),
            Platform(200, SCREEN_HEIGHT - 200, 150, 20),
            DisappearingPlatform(400, SCREEN_HEIGHT - 300, 150, 20),
            MovingPlatform(600, SCREEN_HEIGHT - 250, 150, 20, 550, 750, 2),
            BouncePlatform(750, SCREEN_HEIGHT - 350, 100, 20),
            DisappearingPlatform(300, SCREEN_HEIGHT - 450, 100, 20),
            MovingPlatform(500, SCREEN_HEIGHT - 500, 200, 20, 400, 700, 1),
        ]
        
        self.enemies = [
            Enemy(210, SCREEN_HEIGHT - 230, 200, 350),
            Enemy(410, SCREEN_HEIGHT - 330, 400, 550),
            Enemy(610, SCREEN_HEIGHT - 280, 600, 750),
        ]
        
        self.coins = [
            Coin(250, SCREEN_HEIGHT - 240),
            Coin(450, SCREEN_HEIGHT - 340),
            Coin(650, SCREEN_HEIGHT - 290),
            Coin(800, SCREEN_HEIGHT - 390),
            Coin(350, SCREEN_HEIGHT - 490),
        ]
        
        self.powerups = [
            PowerUp(320, SCREEN_HEIGHT - 240, 'speed'),
            PowerUp(780, SCREEN_HEIGHT - 390, 'jump'),
            PowerUp(520, SCREEN_HEIGHT - 540, 'invulnerable'),
            PowerUp(100, SCREEN_HEIGHT - 140, 'reverse'),
        ]
        
        road_y = SCREEN_HEIGHT - 150

        self.red_coin = RedCoin(SCREEN_WIDTH - 120, road_y - 25)

    def reset_to_platformer_start(self):


        print('[Game] reset_to_platformer_start called')

        self.Total_score = 0
        self.game_mode = 'platformer'
        self.lives = 3
        self.score = 0
        self.last_score_snapshot = 0

        self.player = Player(50, SCREEN_HEIGHT - 200)
        self.car = Car(100, SCREEN_HEIGHT - 180)
        self.obstacles = []
        self.bullets = []
        self.muzzles = []
        self.explosions = []
        self.golden_coin = None

        self.platforms = [
            Platform(0, SCREEN_HEIGHT - 100, SCREEN_WIDTH, 100),
            Platform(200, SCREEN_HEIGHT - 200, 150, 20),
            DisappearingPlatform(400, SCREEN_HEIGHT - 300, 150, 20),
            MovingPlatform(600, SCREEN_HEIGHT - 250, 150, 20, 550, 750, 2),
            BouncePlatform(750, SCREEN_HEIGHT - 350, 100, 20),
            DisappearingPlatform(300, SCREEN_HEIGHT - 450, 100, 20),
            MovingPlatform(500, SCREEN_HEIGHT - 500, 200, 20, 400, 700, 1),
        ]
        self.enemies = [
            Enemy(210, SCREEN_HEIGHT - 230, 200, 350),
            Enemy(410, SCREEN_HEIGHT - 330, 400, 550),
            Enemy(610, SCREEN_HEIGHT - 280, 600, 750),
        ]
        self.coins = [
            Coin(250, SCREEN_HEIGHT - 240),
            Coin(450, SCREEN_HEIGHT - 340),
            Coin(650, SCREEN_HEIGHT - 290),
            Coin(800, SCREEN_HEIGHT - 390),
            Coin(350, SCREEN_HEIGHT - 490),
        ]
        self.powerups = [
            PowerUp(320, SCREEN_HEIGHT - 240, 'speed'),
            PowerUp(780, SCREEN_HEIGHT - 390, 'jump'),
            PowerUp(520, SCREEN_HEIGHT - 540, 'invulnerable'),
            PowerUp(100, SCREEN_HEIGHT - 140, 'reverse'),
        ]
        
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and self.lives <= 0:
                    self.__init__()
                elif event.key == pygame.K_p and self.game_mode == "hill_climb":
                    self.game_mode = "platformer"
                    pygame.display.set_caption("🔥 Devil Mario - Unexpected Chaos! 🔥")
                elif event.key == pygame.K_v:

                    if hasattr(self, 'car') and self.red_coin:
                        cx, cy = self.car.x, self.car.y
                        rx, ry = self.red_coin.x, self.red_coin.y

                        self.car.x, self.car.y = rx, ry
                        self.car.rect.x = int(self.car.x)
                        self.car.rect.y = int(self.car.y)
                        self.red_coin.x, self.red_coin.y = cx, cy
                        self.red_coin.rect.x = int(self.red_coin.x)
                        self.red_coin.rect.y = int(self.red_coin.y)
                elif event.key == pygame.K_f:

                    if self.game_mode == "hill_climb":
                        bx = self.car.x + self.car.width
                        by = self.car.y + 10
                        self.bullets.append(Bullet(bx, by))

                        self.muzzles.append(MuzzleFlash(bx + 6, by + 2))
                        play_sound(SHOOT_SOUND)
                    
    def update(self):
        if self.game_mode == "hill_climb":
            self.update_hill_climb()

        delta = int(self.score - getattr(self, 'last_score_snapshot', 0))
        if delta > 0:
            self.Total_score += delta
            self.last_score_snapshot = self.score

            if self.Total_score > self.high_score:
                self.high_score = int(self.Total_score)
                try:
                    with open(self.highscore_path, 'w') as f:
                        f.write(str(self.high_score))
                except Exception:
                    pass
        elif self.lives > 0:
            self.chaos_timer += 1
            

            for platform in self.platforms:
                platform.update()
                
            self.player.update(self.platforms)
            
            for platform in self.platforms:
                if isinstance(platform, DisappearingPlatform):
                    if self.player.rect.colliderect(platform.rect) and self.player.on_ground:
                        platform.trigger_disappear()
            
            for platform in self.platforms:
                if isinstance(platform, BouncePlatform):
                    if (self.player.rect.colliderect(platform.rect) and 
                        self.player.vel_y > 0 and 
                        self.player.rect.bottom <= platform.rect.top + 20):
                        self.player.vel_y = JUMP_STRENGTH * 2
                        play_sound(POWERUP_SOUND)
            
            for enemy in self.enemies:
                enemy.update()
                
            if self.player.invulnerable_timer <= 0:
                for enemy in self.enemies:
                    if self.player.rect.colliderect(enemy.rect):
                        self.lives -= 1
                        self.player.invulnerable_timer = 120
                        self.player.x = 50
                        self.player.y = SCREEN_HEIGHT - 200
                        self.player.vel_x = 0
                        self.player.vel_y = 0
                        play_sound(HIT_SOUND)
                        
            for coin in self.coins[:]:
                if self.player.rect.colliderect(coin.rect):
                    self.coins.remove(coin)
                    self.score += 100
                    play_sound(COIN_SOUND)
                    
                if self.red_coin and self.player.rect.colliderect(self.red_coin.rect):
                    self.score += 500
                    self.game_mode = "hill_climb"
                    road_y = SCREEN_HEIGHT - 150
                    forward_offset = 200
                    coin_x = int(max(self.car.x - forward_offset, 0))
                    self.red_coin = RedCoin(coin_x, road_y - 25)
                    pygame.display.set_caption("🔥 DevilCoder - Kuldeep singh 🔥")
                    play_sound(POWERUP_SOUND)
                    
            for powerup in self.powerups[:]:
                if self.player.rect.colliderect(powerup.rect):
                    self.powerups.remove(powerup)
                    play_sound(POWERUP_SOUND)
                    if powerup.type == 'speed':
                        self.player.speed_boost_timer = 300
                        self.score += 50
                    elif powerup.type == 'jump':
                        self.player.big_jump_timer = 300
                        self.score += 50
                    elif powerup.type == 'invulnerable':
                        self.player.invulnerable_timer = 300
                        self.score += 50
                    elif powerup.type == 'reverse':
                        self.player.reverse_controls = 240
                        self.score -= 25
                        play_sound(HIT_SOUND)
                        
            if self.chaos_timer % 900 == 0:
                chaos_event = random.randint(1, 3)
                if chaos_event == 1:
                    self.player.reverse_controls = 180
                elif chaos_event == 2:
                    self.player.speed_boost_timer = 240
                elif chaos_event == 3:
                    self.player.x = random.randint(100, SCREEN_WIDTH - 100)
                    self.player.y = SCREEN_HEIGHT - 300
                    
            if self.player.y > SCREEN_HEIGHT:
                self.lives -= 1
                self.player.x = 50
                self.player.y = SCREEN_HEIGHT - 200
                self.player.vel_x = 0
                self.player.vel_y = 0

    def update_hill_climb(self):
        if self.car.fuel > 0:
            self.car.update()
            self.obstacle_timer += 1
            if self.obstacle_timer > 180:
                self.obstacle_timer = 0
                spawn_x = int(self.car.x + SCREEN_WIDTH + random.randint(50, 300))
                spawn_y = SCREEN_HEIGHT - 180
                speed = 4 + random.random() * 2
                self.obstacles.append(ObstacleCar(spawn_x, spawn_y, speed))
            for obs in self.obstacles[:]:
                obs.update()
                if obs.x + obs.width < self.car.x - SCREEN_WIDTH:
                    self.obstacles.remove(obs)
                else:
                    car_rect_world = pygame.Rect(self.car.x, self.car.y, self.car.width, self.car.height)
                    if car_rect_world.colliderect(obs.rect):
                        self.lives = 0
                        play_sound(HIT_SOUND)
                        return
            for b in self.bullets[:]:
                b.update()
                if b.x > self.car.x + SCREEN_WIDTH * 2:
                    self.bullets.remove(b)
                    continue
                for obs in self.obstacles[:]:
                    if b.rect.colliderect(obs.rect):
                        try:
                            self.obstacles.remove(obs)
                        except ValueError:
                            pass
                        try:
                            self.bullets.remove(b)
                        except ValueError:
                            pass
                        self.explosions.append(Explosion(obs.x + obs.width/2, obs.y + obs.height/2))
                        play_sound(BLAST_SOUND)
                        self.score += 200
                        play_sound(COIN_SOUND)
                        break

            if self.bullet_cooldown > 0:
                self.bullet_cooldown -= 1
            if self.red_coin:
                car_rect_world = pygame.Rect(self.car.x, self.car.y, self.car.width, self.car.height)
                if car_rect_world.colliderect(self.red_coin.rect):
                    self.score += 500
                    self.red_coin = None
                    self.game_mode = "platformer"
                    pygame.display.set_caption("🔥 DevilCoder -  singh 🔥")
                    play_sound(POWERUP_SOUND)
            if self.car.fuel <= 0:
                self.lives -= 1
                if self.lives > 0:
                    self.car = Car(100, SCREEN_HEIGHT - 180)
            if self.golden_coin is None and self.car.distance >= 800:
                coin_x = int(self.car.x + SCREEN_WIDTH * 0.6)
                road_y = SCREEN_HEIGHT - 150
                self.golden_coin = GoldenCoin(coin_x, road_y - 25)
            if self.golden_coin:
                car_rect_world = pygame.Rect(self.car.x, self.car.y, self.car.width, self.car.height)
                if car_rect_world.colliderect(self.golden_coin.rect):
                    self.score += 2000
                    play_sound(POWERUP_SOUND)
                    self.golden_coin = None
                    try:
                        dino_ret = dinosaur_main(self)
                        dino_score = None
                        restart_flag = False
                        try:
                            if isinstance(dino_ret, tuple) and len(dino_ret) == 2:
                                dino_score, restart_flag = dino_ret
                            elif isinstance(dino_ret, (int, float)):
                                dino_score = dino_ret
                        except Exception:
                            pass
                        try:
                            print(f'[update_hill_climb] dino_ret={dino_ret}')
                            if isinstance(dino_score, (int, float)):
                                self.Total_score += int(dino_score)
                        except Exception:
                            pass
                        if restart_flag:
                            print('[update_hill_climb] restart_flag True -> resetting to platformer start')
                            try:
                                self.reset_to_platformer_start()
                                print('[update_hill_climb] reset_to_platformer_start completed')
                            except Exception:
                                print('[update_hill_climb] reset helper failed, using fallback')
                                self.game_mode = 'platformer'
                                self.lives = 3
                                self.score = 0
                                self.last_score_snapshot = 0
                        pygame.init()
                        pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
                        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
                        pygame.display.set_caption("🔥 DevilCoder - Kuldeep singh 🔥")
                    except Exception as e:
                        print('Failed to launch embedded dinosaur game:', e)
                    
    def draw(self):
        if self.game_mode == "hill_climb":
            self.draw_hill_climb()
        else:
            self.draw_platformer()
            
    def draw_platformer(self):
        if self.player.reverse_controls > 0:
            self.screen.fill((200, 100, 200))
        else:
            self.screen.fill((135, 206, 235))

        for platform in self.platforms:
            platform.draw(self.screen)

        for enemy in self.enemies:
            enemy.draw(self.screen)

        for coin in self.coins:
            coin.draw(self.screen)

        if self.red_coin:
            self.red_coin.update()
            self.red_coin.draw(self.screen)

        for powerup in self.powerups:
            powerup.draw(self.screen)

        if self.lives > 0:
            self.player.draw(self.screen)

        Total_text = self.font.render(f"Score: {self.Total_score}", True, BLACK)
        self.screen.blit(Total_text, (10, 10))
        high_text = self.font.render(f"Top: {self.high_score}", True, BLACK)
        high_x = SCREEN_WIDTH // 2 - high_text.get_width() // 2
        self.screen.blit(high_text, (high_x, 10))

        effect_y = 60
        if self.player.speed_boost_timer > 0:
            effect_text = self.font.render("SPEED BOOST!", True, ORANGE)
            self.screen.blit(effect_text, (10, effect_y))
            effect_y += 30
        if self.player.big_jump_timer > 0:
            effect_text = self.font.render("BIG JUMP!", True, LIME)
            self.screen.blit(effect_text, (10, effect_y))
            effect_y += 30
        if self.player.invulnerable_timer > 0:
            effect_text = self.font.render("INVULNERABLE!", True, WHITE)
            self.screen.blit(effect_text, (10, effect_y))
            effect_y += 30
        if self.player.reverse_controls > 0:
            effect_text = self.font.render("CONTROLS REVERSED!", True, PURPLE)
            self.screen.blit(effect_text, (10, effect_y))

        if self.lives <= 0:
            game_over_text = self.font.render("GAME OVER! Press R to restart", True, RED)
            text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            self.screen.blit(game_over_text, text_rect)

        if self.lives > 0:
            instruction_text = self.font.render("FIND THE GLOWING RED COIN to switch game!", True, BLACK)
            self.screen.blit(instruction_text, (10, SCREEN_HEIGHT - 60))
            warning_text = self.font.render(" ", True, DARK_RED)
            self.screen.blit(warning_text, (10, SCREEN_HEIGHT - 30))
            
    def draw_hill_climb(self):
        self.screen.fill((135, 206, 235))  
        
        sky_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT // 2))
        for y in range(SCREEN_HEIGHT // 2):
            color_ratio = y / (SCREEN_HEIGHT // 2)
            sky_color = (
                int(135 + (200 - 135) * color_ratio),
                int(206 + (230 - 206) * color_ratio),
                int(235 + (255 - 235) * color_ratio)
            )
            pygame.draw.line(sky_surface, sky_color, (0, y), (SCREEN_WIDTH, y))
        self.screen.blit(sky_surface, (0, 0))
        
        for i in range(8):
            cloud_x = (50 + i * 200 - self.car.camera_x * 0.3) % (SCREEN_WIDTH + 200) - 100
            cloud_y = 80 + (i % 3) * 30
            if -100 <= cloud_x <= SCREEN_WIDTH + 100:
                pygame.draw.circle(self.screen, WHITE, (int(cloud_x), cloud_y), 30)
                pygame.draw.circle(self.screen, WHITE, (int(cloud_x - 20), cloud_y), 20)
                pygame.draw.circle(self.screen, WHITE, (int(cloud_x + 20), cloud_y), 20)
        
        hill_points = []
        start_x = int(self.car.camera_x * 0.5) - 100
        for x in range(start_x, start_x + SCREEN_WIDTH + 200, 50):
            screen_x = x - self.car.camera_x * 0.5
            if -100 <= screen_x <= SCREEN_WIDTH + 100:
                hill_height = SCREEN_HEIGHT - 200 + int(50 * math.sin(x * 0.008))
                hill_points.append((screen_x, hill_height))
        
        if len(hill_points) > 1:
            hill_points.append((SCREEN_WIDTH + 100, SCREEN_HEIGHT))
            hill_points.append((-100, SCREEN_HEIGHT))
            pygame.draw.polygon(self.screen, (34, 139, 34), hill_points)
        
        road_y = SCREEN_HEIGHT - 150
        pygame.draw.rect(self.screen, (50, 50, 50), (0, road_y, SCREEN_WIDTH, 150)) 
        pygame.draw.rect(self.screen, GREEN, (0, road_y - 20, SCREEN_WIDTH, 20))  
        
        marking_start = int(self.car.camera_x) % 100
        for x in range(-marking_start, SCREEN_WIDTH + 100, 100):
            pygame.draw.rect(self.screen, YELLOW, (x, road_y + 70, 50, 5))
        
        tree_start = int(self.car.camera_x * 0.8)
        for i in range(15):
            tree_world_x = 80 + i * 120 + tree_start
            tree_x = tree_world_x - self.car.camera_x * 0.8
            if -50 <= tree_x <= SCREEN_WIDTH + 50:
                tree_y = SCREEN_HEIGHT - 180
                pygame.draw.rect(self.screen, BROWN, (int(tree_x - 5), tree_y, 10, 30))
                pygame.draw.circle(self.screen, (0, 100, 0), (int(tree_x), tree_y), 15)
        
        if self.lives > 0:
            self.car.draw(self.screen, self.car.camera_x)
        for obs in self.obstacles:
            obs.draw(self.screen, self.car.camera_x)
        for b in self.bullets:
            b.draw(self.screen, self.car.camera_x)
        for m in self.muzzles[:]:
            m.update()
            m.draw(self.screen, self.car.camera_x)
            if m.timer > m.lifetime:
                self.muzzles.remove(m)
        for e in self.explosions[:]:
            e.update()
            e.draw(self.screen, self.car.camera_x)
            if e.timer > e.max_time:
                self.explosions.remove(e)
        if self.golden_coin:
            self.golden_coin.update()
            self.golden_coin.draw(self.screen, self.car.camera_x)
            
        if hasattr(self.car, 'vel_x') and self.car.vel_x > 2:
            for i in range(4):
                smoke_x = self.car.x - self.car.camera_x - 20 - i * 8
                smoke_y = self.car.y + 20 + random.randint(-3, 3)
                if -30 <= smoke_x <= SCREEN_WIDTH + 30:
                    pygame.draw.circle(self.screen, (100, 100, 100), (int(smoke_x), int(smoke_y)), 4 - i)
            
        ui_font = pygame.font.Font(None, 32)
        score_text = ui_font.render(f"Score: {self.score}", True, BLACK)
        lives_text = ui_font.render(f"Lives: {self.lives}", True, BLACK)
        fuel_text = ui_font.render(f"Fuel: {int(self.car.fuel)}", True, BLACK)
        distance_text = ui_font.render(f"Distance: {int(self.car.distance)}m", True, BLACK)
        speed_text = ui_font.render(f"Speed: {abs(int(self.car.vel_x * 15))} km/h", True, BLACK)
        
        Total_text = ui_font.render(f"Score: {self.Total_score}", True, BLACK)
        self.screen.blit(Total_text, (10, 10))
        high_text = ui_font.render(f"Top: {self.high_score}", True, BLACK)
        high_x = SCREEN_WIDTH // 2 - high_text.get_width() // 2
        self.screen.blit(high_text, (high_x, 10))
        self.screen.blit(score_text, (10, 45))
        self.screen.blit(lives_text, (10, 80))
        self.screen.blit(fuel_text, (10, 115))
        self.screen.blit(distance_text, (10, 150))
        self.screen.blit(speed_text, (10, 185))


        if self.red_coin:

            draw_x = int(self.red_coin.x - self.car.camera_x)
            draw_y = int(self.red_coin.y)

            self.red_coin.update()
            glow_size = 12 + int(3 * math.sin(self.red_coin.glow_timer * 0.2))
            pygame.draw.circle(self.screen, RED, (draw_x + 12, draw_y + 12), glow_size)
            pygame.draw.circle(self.screen, DARK_RED, (draw_x + 12, draw_y + 12), glow_size, 3)
            pygame.draw.circle(self.screen, WHITE, (draw_x + 12, draw_y + 12), 4)
        

        fuel_bar_width = 200
        fuel_ratio = max(0, self.car.fuel / 100)
        fuel_color = GREEN if fuel_ratio > 0.3 else (ORANGE if fuel_ratio > 0.1 else RED)
        
        pygame.draw.rect(self.screen, BLACK, (SCREEN_WIDTH - fuel_bar_width - 25, 15, fuel_bar_width + 10, 30))
        pygame.draw.rect(self.screen, fuel_color, (SCREEN_WIDTH - fuel_bar_width - 20, 20, fuel_bar_width * fuel_ratio, 20))
        pygame.draw.rect(self.screen, BLACK, (SCREEN_WIDTH - fuel_bar_width - 20, 20, fuel_bar_width, 20), 2)
        
        fuel_label = ui_font.render("FUEL", True, BLACK)
        self.screen.blit(fuel_label, (SCREEN_WIDTH - fuel_bar_width - 20, 50))
        

        if self.lives <= 0:
            game_over_text = self.font.render("GAME OVER! Press R to restart", True, RED)
            text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            self.screen.blit(game_over_text, text_rect)
            

        if self.lives > 0:
            instruction_text = self.font.render("RIGHT/D = Accelerate, LEFT/A = Brake/Reverse, P = Back to Platformer", True, BLACK)
            self.screen.blit(instruction_text, (10, SCREEN_HEIGHT - 30))
        

        pygame.display.flip()
        
    def run(self):
        print("🎮 Starting Devil Mario Game!")
        while self.running:
            self.handle_events()
            self.update()
            self.draw()

            if self.game_mode == "platformer":
                pygame.display.flip()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()