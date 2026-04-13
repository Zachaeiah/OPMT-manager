import inspect
from typing import Any, Callable, Dict, Type, TypeVar
from .exceptions import DependencyNotFoundError

T = TypeVar("T")

# -------------------------
# Named injection helper
# -------------------------
class Inject:
    """ Helper class to specify named dependencies for injection in constructor parameters.
    """
    def __init__(self, cls: Type, name: str | None = None):
        """ Helper class to specify named dependencies for injection in constructor parameters.

        Args:
            cls (Type): Class to inject
            name (str | None, optional): Optional name for the provider (for multiple providers of the same class). Defaults to None.
        """
        self.cls = cls
        self.name = name


class Container:
    """A simple dependency injection container that supports constructor injection and singleton management.
    It allows you to register providers for classes and resolve instances of those classes, automatically
    """
    def __init__(self) -> None:
        """ Constructor for Container class
        """

        
        self._providers: Dict[
            tuple[Type, str | None],
            tuple[Callable[..., Any], bool]
        ] = {}

        self._singletons: Dict[
            tuple[Type, str | None],
            Any
        ] = {}

        self._resolving: set[
            tuple[Type, str | None]
        ] = set()

        # NEW: track full resolution chain
        self._resolving_stack: list[
            tuple[Type, str | None]
        ] = []

    # -------------------------
    # Registration
    # -------------------------
    def register(
        self,
        cls: Type[T],
        provider: Callable[..., T] | Type[T],
        singleton: bool = False,
        name: str | None = None
    ) -> None:
        """ Register a provider for a given class

        Args:
            cls (Type[T]): Class to register provider for
            provider (Callable[..., T] | Type[T]): Provider function or class
            singleton (bool, optional): Whether to use singleton pattern. Defaults to False.
            name (str | None, optional): Optional name for the provider (for multiple providers of the same class). Defaults to None.
        """
        key = (cls, name)
        self._providers[key] = (provider, singleton)

    def register_instance(self, cls: Type[T], instance: T, name) -> None:
        """ Register a specific instance for a given class (singleton)

        Args:
            cls (Type[T]): Class to register instance for
            instance (T): Instance to register
            name (str | None, optional): Optional name for the provider (for multiple providers of the same class). Defaults to None.
        """
        key = (cls, name)
        self._singletons[key] = instance

    # -------------------------
    # Resolution
    # -------------------------
    def resolve(self, cls: Type[T], name: str | None = None) -> T:
        """ Resolve an instance of the given class, using registered providers or constructor injection.

        Args:
            cls (Type[T]): Class to resolve
            name (str | None, optional): Optional name for the provider (for multiple providers of the same class). Defaults to None.

        Raises:
            RuntimeError: If a circular dependency is detected during resolution
            DependencyNotFoundError: If no provider is registered for the class and it cannot be constructed

        Returns:
            T: Instance of the class returned by the provider or constructed directly
        """
        
        key = (cls, name)

        if key in self._singletons:
            return self._singletons[key]

        if key in self._resolving:
            raise RuntimeError(f"Circular dependency detected: {cls}:{name}")

        # Mark this class as currently being resolved to detect circular dependencies
        self._resolving.add(key)
        self._resolving_stack.append(key)

        try:
            # -------------------------
            # Use registered provider
            # -------------------------
            if key in self._providers:
                provider, singleton = self._providers[key]

                if isinstance(provider, type):
                    instance: T = self._construct(provider)
                else:
                    instance: T = provider()

                if singleton:
                    self._singletons[key] = instance

                return instance

            # -------------------------
            # Fallback: auto construct
            # -------------------------
            try:
                return self._construct(cls)

            except Exception as e:
                raise DependencyNotFoundError(
                    cls,
                    name,
                    path=self._resolving_stack.copy(),
                    available=list(self._providers.keys())
                ) from e

        except DependencyNotFoundError as e:
            # propagate with full path
            raise DependencyNotFoundError(
                cls,
                name,
                path=self._resolving_stack.copy(),
                available=list(self._providers.keys())
            ) from e

        finally:
            self._resolving.remove(key)
            self._resolving_stack.pop()

    # -------------------------
    # Auto constructor injection
    # -------------------------
    def _construct(self, cls: Type[T]) -> T:
        """ Construct an instance of the given class by resolving its constructor dependencies.

        Args:
            cls (Type[T]): Class to construct

        Raises:
            TypeError: If any constructor parameter is missing a type annotation

        Returns:
            T: Instance of the class constructed with resolved dependencies
        """
        sig: inspect.Signature = inspect.signature(cls.__init__)
        kwargs: dict[str, object] = {}

        # Resolve each parameter in the constructor by looking up its type annotation and resolving that type from the container
        for name, param in sig.parameters.items():
            # Skip 'self' parameter
            if name == "self":
                continue
            
            # If the parameter is missing a type annotation, we cannot resolve it, so we raise an error
            if param.annotation is inspect.Parameter.empty:
                raise TypeError(
                    f"Missing type annotation for '{name}' in {cls}"
                )
            
            ann = param.annotation

            # If the annotation is an Inject instance, we need to resolve the specified class and name from the container
            if isinstance(ann, Inject):
                dependency = self.resolve(ann.cls, ann.name)
            else:
                dependency = self.resolve(ann)
                
            kwargs[name] = dependency

        return cls(**kwargs)
    
    def validate(self, fail_fast: bool = True) -> list[Exception]:
        """
        Validate the container by attempting to resolve all registered providers.

        Args:
            fail_fast (bool): If True, raise on first error.
                            If False, collect all errors.

        Returns:
            list[Exception]: List of validation errors (empty if valid)
        """
        errors: list[Exception] = []

        for (cls, name), (provider, _) in self._providers.items():
            try:
                # force fresh resolution (ignore cached singletons)
                self._validate_resolve(cls, name)

            except Exception as e:
                if fail_fast:
                    raise e
                errors.append(e)

        return errors
    
    def _validate_resolve(self, cls: Type[T], name: str | None):
        """Internal resolve used only for validation.
        Does not mutate singleton cache.

        Args:
            cls (Type[T]): _description_
            name (str | None): _description_

        Raises:
            RuntimeError: _description_
            DependencyNotFoundError: _description_
        """
        key = (cls, name)

        if key in self._resolving:
            raise RuntimeError(f"Circular dependency detected during validation: {cls}:{name}")

        self._resolving.add(key)
        self._resolving_stack.append(key)

        try:
            if key in self._providers:
                provider, _ = self._providers[key]

                if isinstance(provider, type):
                    self._validate_construct(provider)
                else:
                    provider()

            else:
                self._validate_construct(cls)

        except Exception as e:
            raise DependencyNotFoundError(
                cls,
                name,
                path=self._resolving_stack.copy(),
                available=list(self._providers.keys())
            ) from e

        finally:
            self._resolving.remove(key)
            self._resolving_stack.pop()

    def _validate_construct(self, cls: Type[T]):
        """_summary_

        Args:
            cls (Type[T]): _description_

        Raises:
            TypeError: _description_
        """
        sig = inspect.signature(cls.__init__)

        for name, param in sig.parameters.items():
            if name == "self":
                continue

            if param.annotation is inspect.Parameter.empty:
                raise TypeError(
                    f"[VALIDATION] Missing type annotation for '{name}' in {cls}"
                )

            ann = param.annotation

            if isinstance(ann, Inject):
                self._validate_resolve(ann.cls, ann.name)
            else:
                self._validate_resolve(ann, None)
    
    def create_scope(self) -> "Container":
        """ Create a new scope (child container) that inherits providers and singletons from the parent container. 
        This allows for scoped dependencies in sub-operations or tasks.

        Returns:
            Container: A new child container with the same providers and singletons as the parent container
        """
        child = Container()
        child._providers = self._providers.copy()
        child._singletons = self._singletons.copy()
        return child

    # -------------------------
    # Utilities
    # -------------------------
    def has(self, cls: Type, name: str = None) -> bool:
        """ Check if a provider is registered for a given class

        Args:
            cls (Type): Class to check for registered provider
            name (str, optional): Optional name for the provider (for multiple providers of the same class). Defaults to None.

        Returns:
            bool: True if a provider is registered for the class, False otherwise
        """
        key = (cls, name)
        return key in self._providers or key in self._singletons

    def clear(self) -> None:
        """ Clear all registered providers and singletons from the container
        """
        self._providers.clear()
        self._singletons.clear()