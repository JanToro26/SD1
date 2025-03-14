import Pyro4

@Pyro4.expose
@Pyro4.behavior(instance_mode="single")
class Observer:
    list=[]
    def register(self, obs):
        if (obs not in list):
            list.append(obs)
            return f"Afegit"
        else:
            return f"Ja hi era"
        
    def unregister(self, obs):
        if (obs in list):
            list.remove(obs)
            return f"Eliminat"
        else:
            return f"No hi era"
        
    def notify(self, state):
        for obs in list:
            obs.update(state)

def main():
    

if __name__ == "__main__":
    main()