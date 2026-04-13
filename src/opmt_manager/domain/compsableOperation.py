from opmt_manager.container import Container
from .operation import Operation
from .compsableTask import ComposableTask
from typing import Type, TypeVar, Callable

T = TypeVar("T")


class ComposableOperation(Operation):
    def __init__(self, name: str, container: Container | None = None):
        """  A ComposableOperation is an Operation that has an associated dependency injection container.

        Args:
            name (str): Name of the operation
            container (Container | None, optional): Optional external container to use for dependency management. Defaults
        """
        super().__init__(name)

        # root container for the entire operation
        self.container: Container = container or Container()

    def register(
        self,
        cls: Type[T],
        provider: Callable[..., T] | Type[T],
        singleton: bool = False,
        name: str | None = None
    ) -> None:
        """ Register a provider for a given class in the operation's container

        Args:
            cls (Type[T]): Class to register
            provider (Callable[..., T] | Type[T]): Provider function or class to register
            singleton (bool, optional): Whether to use singleton pattern for this provider. Defaults to False.
            name (str | None, optional): Name for the provider. Defaults to None.
        """
        self.container.register(cls, provider, singleton=singleton, name=name)

    def register_instance(self, cls: Type[T], instance: T, name: str | None = None  ) -> None:
        """ Register a specific instance for a given class in the operation

        Args:
            cls (Type[T]): Class to register instance for
            instance (T): Instance to register
            name (str | None, optional): Name for the instance. Defaults to None.
        """
        self.container.register_instance(cls, instance, name=name)

    def get(self, cls: Type[T], name: str | None = None) -> T:
        """ Get an instance of the given class from the operation's container

        Args:
            cls (Type[T]): Class to get instance of
            name (str | None, optional): Name of the instance to get. Defaults to None.

        Returns:
            T: Instance of the class returned by the container
        """
        return self.container.resolve(cls, name=name)

    def has(self, cls: Type, name: str | None = None) -> bool:
        """ Check if the operation's container has a provider for the given class

        Args:
            cls (Type): Class to check for provider in the container
            name (str | None, optional): Name of the provider to check. Defaults to None.

        Returns:
            bool: True if the container has a provider for the class, False otherwise
        """
        return self.container.has(cls, name=name)

    def create_task(self, name: str, duration: float) -> ComposableTask:
        """ Create a new ComposableTask with the same container as the operation. This allows the task to share dependencies registered in the operation's container.

        Args:
            name (str): Name of the task
            duration (float): Duration of the task

        Returns:
            ComposableTask: A new ComposableTask instance with the same container as the operation
        """
        return ComposableTask(name, duration, container=self.container)

    def create_scope(self) -> Container:
        """ Create a new scope (child container) from the operation's container. This can be used to create a new scope for a sub-operation or task, allowing for scoped dependencies.

        Returns:
            Container: A new child container created from the operation's container
        """
        return self.container.create_scope()