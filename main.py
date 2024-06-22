import pygame
import sys
import numpy as np

# game constants
WIDTH = 1000
HEIGHT = 800

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
PURPLE = (90, 99, 156)
GREEN = (129, 162, 99)
RED = (166, 16, 30)
GREY = (230, 230, 230)
YELLOW = (190, 175, 50)
BG_COLOR = WHITE

RADIUS = 5
VEL_X = 0
VEL_Y = 0

class Blood():
    def __init__(self, screen, x, y, color=BLACK, radius=RADIUS, velocity=[VEL_X, VEL_Y], randomize=False):
        self.screen = screen
        self.color = color
        self.radius = radius
        self.pos = np.array([x, y], dtype=np.float64)
        self.vel = np.asarray(velocity, dtype=np.float64)
        self.WIDTH = WIDTH
        self.HEIGHT = HEIGHT
        self.kill_switch = False
        self.recovered_container = False
        self.randomize = randomize

    def update(self):
        self.pos += self.vel

        x, y = self.pos

        # boundary conditions
        if x < 0 or x > self.WIDTH:
            self.vel[0] = -self.vel[0]  # Reverse the x-velocity

        if y < 0 or y > self.HEIGHT:
            self.vel[1] = -self.vel[1]  # Reverse the y-velocity

        # normalize the velocity
        vel_norm = np.linalg.norm(self.vel)
        if vel_norm > 3:
            self.vel /= vel_norm

        if self.randomize:
            self.vel += np.random.rand(2) * 2 - 1

        if self.kill_switch:
            self.cycle_to_fate -= 1

            if self.cycle_to_fate <= 0:
                self.kill_switch = False

                if self.mortality_rate > np.random.rand():
                    return True  # kill this object
                else:
                    self.recovered_container = True

        return False  # don't kill this object

    def respawn(self, color):
        return Blood(self.screen, self.pos[0], self.pos[1], color=color, velocity=self.vel)

    def killSwitch(self, cycle_to_fate=20, mortality_rate=0.2):
        self.kill_switch = True
        self.cycle_to_fate = cycle_to_fate
        self.mortality_rate = mortality_rate

    def draw(self):
        pygame.draw.circle(self.screen, self.color, (int(self.pos[0]), int(self.pos[1])), self.radius)


def check_collision(list1, list2):
    collided = []
    for obj1 in list1:
        for obj2 in list2:
            distance = np.linalg.norm(obj1.pos - obj2.pos)
            if distance < obj1.radius + obj2.radius:
                collided.append(obj1)
                break
    return collided


class Simulation:
    def __init__(self):
        self.WIDTH = WIDTH
        self.HEIGHT = HEIGHT

        self.susceptible_container = []
        self.infected_container = []
        self.recovered_container = []
        self.population_container = []

        self.n_susceptible_container = 50
        self.n_infected_container = 1

        self.cycle_to_fate = 20
        self.mortality_rate = 0.1

    def start(self, randomize=False):
        pygame.init()
        screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))

        self.N = self.n_susceptible_container + self.n_infected_container

        for i in range(self.n_susceptible_container):
            x = np.random.randint(0, self.WIDTH + 1)
            y = np.random.randint(0, self.HEIGHT + 1)
            vel = np.random.rand(2) * 2 - 1

            blood = Blood(screen, x, y, color=RED, velocity=vel, randomize=randomize)
            self.susceptible_container.append(blood)
            self.population_container.append(blood)

        for i in range(self.n_infected_container):
            x = np.random.randint(0, self.WIDTH + 1)
            y = np.random.randint(0, self.HEIGHT + 1)
            vel = np.random.rand(2) * 2 - 1

            blood = Blood(screen, x, y, color=GREEN, velocity=vel, randomize=randomize)
            self.infected_container.append(blood)
            self.population_container.append(blood)

        stats = pygame.Surface((WIDTH//5, HEIGHT//5))
        stats.fill(GREY)
        stats.set_alpha(230)
        stats_pos = (WIDTH//40, HEIGHT//40)

        clock = pygame.time.Clock()
        iteration_count = 0
        time_step = 1 / 30  # Each iteration represents 1/30th of a second (30 FPS)

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            screen.fill(BG_COLOR)

            # update stats
            stats_height = stats.get_height()
            stats_width = stats.get_width()

            n_inf_now = len(self.infected_container)
            n_pop_now = len(self.population_container)
            n_rec_now = len(self.recovered_container)
            n_sus_now = len(self.susceptible_container)
            n_dead_now = self.N - n_pop_now

            curr_time = iteration_count * time_step
            if curr_time >= stats_width:
                curr_time = stats_width - 1

            # Calculate the heights of the stacked areas
            y_sus = int((n_sus_now / self.N) * stats_height)
            y_inf = int((n_inf_now / self.N) * stats_height)
            y_rec = int((n_rec_now / self.N) * stats_height)

            stats_graph = pygame.PixelArray(stats)

            # Draw the areas, starting from the top
            stats_graph[int(curr_time), stats_height - y_sus:stats_height] = pygame.Color(*RED)
            stats_graph[int(curr_time), stats_height - y_sus - y_inf:stats_height - y_sus] = pygame.Color(*GREEN)
            stats_graph[int(curr_time), stats_height - y_sus - y_inf - y_rec:stats_height - y_sus - y_inf] = pygame.Color(*PURPLE)

            # List to track bloods that need to be killed
            blood_to_kill = []

            # Update and draw bloods
            for blood in self.population_container:
                if blood.update():
                    blood_to_kill.append(blood)
                else:
                    blood.draw()

            # Remove bloods that need to be killed
            for blood in blood_to_kill:
                if blood in self.susceptible_container:
                    self.susceptible_container.remove(blood)
                if blood in self.infected_container:
                    self.infected_container.remove(blood)
                self.population_container.remove(blood)

            # New infections
            collided_bloods = check_collision(self.susceptible_container, self.infected_container)

            # Collision between infected_container and susceptible_container bloods
            for blood in collided_bloods:
                self.susceptible_container.remove(blood)
                self.population_container.remove(blood)
                new_blood = blood.respawn(GREEN)
                new_blood.vel *= -1
                new_blood.killSwitch(self.cycle_to_fate, self.mortality_rate)
                self.infected_container.append(new_blood)
                self.population_container.append(new_blood)

            # Recovered_container bloods
            recovered_blood = []
            for blood in self.infected_container:
                if blood.recovered_container:
                    new_blood = blood.respawn(PURPLE)
                    self.recovered_container.append(new_blood)
                    self.population_container.append(new_blood)
                    recovered_blood.append(blood)

            for blood in recovered_blood:
                self.infected_container.remove(blood)
                self.population_container.remove(blood)

            del stats_graph
            stats.unlock()
            screen.blit(stats, stats_pos)

            pygame.display.flip()
            clock.tick(30)

            iteration_count += 1

        pygame.quit()


if __name__ == '__main__':
    pygame.display.set_caption('Infection Simulation')
    pygame.display.set_icon(pygame.image.load('./assets/icon.png'))
    covid = Simulation()
    covid.n_susceptible_container = 200
    covid.cycle_to_fate = 200
    covid.mortality_rate = 0.1
    covid.start(randomize=True)
