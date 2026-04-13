from typing import Type, TypeVar, Callable
from opmt_manager.container import Container
from .task import Task

T = TypeVar("T")


class ComposableTask(Task):
    """ A ComposableTask is a Task that has an 
    associated dependency injection container.

    Args:
        Task (_type_): Base Task class that ComposableTask extends
    """
    def __init__(
        self,
        name: str,
        duration: float,
        container: Container | None = None
    ):
        """ The ComposableTask is a Task that has an 
        associated dependency injection container. 
        This allows it to manage its own dependencies and 
        provide them to successor tasks in the operation 
        graph. It also supports creating child scopes for 
        isolated execution contexts.

        Args:
            name (str): Name of the task
            duration (float): Duration of the task
            container (Container | None, optional): 
            Optional external container to use for 
            dependency management. If not provided, a new 
            container will be created. Defaults to None.
        """
        super().__init__(name, duration)

        # allow external container injection (important for graph execution)
        self.container: Container = container or Container()

    def register(
        self,
        cls: Type[T],
        provider: Callable[..., T] | Type[T],
        singleton: bool = False,
        name: str | None = None
    ) -> None:
        """ Register a provider for a given class in the task's container

        Args:
            cls (Type[T]): Class to register
            provider (Callable[..., T] | Type[T]): Provider function or class to register
            singleton (bool, optional): Whether to use singleton pattern for this provider. Defaults to False.
            name (str | None, optional): Name for the provider. Defaults to None.
        """
        self.container.register(cls, provider, singleton=singleton, name=name)

    def register_instance(self, cls: Type[T], instance: T, name: str | None = None) -> None:
        """ Register a specific instance for a given class in the task

        Args:
            cls (Type[T]): Class to register instance for
            instance (T): Instance to register for the class
            name (str | None, optional): Name for the instance. Defaults to None.
        """
        self.container.register_instance(cls, instance, name=name)

    def get(self, cls: Type[T], name: str | None = None) -> T:
        """ Get an instance of the given class from the task's container

        Args:
            cls (Type[T]): Class to get instance of
            name (str | None, optional): Name of the instance to get. Defaults to None.

        Returns:
            T: Instance of the class returned by the container
        """
        return self.container.resolve(cls, name=name)

    def has(self, cls: Type) -> bool:
        """ Check if the task's container has a provider for the given class

        Args:
            cls (Type): Class to check for provider in the container

        Returns:
            bool: True if the container has a provider for the class, False otherwise
        """
        return self.container.has(cls)

    def create_scope(self) -> Container:
        """Create a child container for isolated execution."""
        return self.container.create_scope()