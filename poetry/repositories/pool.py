from typing import List
from typing import Optional

from poetry.utils._compat import OrderedDict

from .base_repository import BaseRepository
from .exceptions import PackageNotFound
from .repository import Repository


class Pool(BaseRepository):
    def __init__(
        self, repositories=None, ignore_repository_names=False
    ):  # type: (Optional[List[Repository]], bool) -> None
        if repositories is None:
            repositories = []

        self._repositories = OrderedDict()

        for repository in repositories:
            self.add_repository(repository)

        self._ignore_repository_names = ignore_repository_names

        super(Pool, self).__init__()

    @property
    def repositories(self):  # type: () -> List[Repository]
        return list(self._repositories.values())

    def add_repository(self, repository):  # type: (Repository) -> Pool
        """
        Adds a repository to the pool.
        """
        self._repositories[repository.name] = repository

        return self

    def remove_repository(self, repository_name):  # type: (str) -> Pool
        if repository_name in self._repositories:
            del self._repositories[repository_name]

        return self

    def has_package(self, package):
        raise NotImplementedError()

    def package(
        self, name, version, extras=None, repository=None
    ):  # type: (str, str, List[str], str) -> Package
        if (
            repository is not None
            and repository not in self._repositories
            and not self._ignore_repository_names
        ):
            raise ValueError('Repository "{}" does not exist.'.format(repository))

        if repository is not None and not self._ignore_repository_names:
            try:
                return self._repositories[repository].package(
                    name, version, extras=extras
                )
            except PackageNotFound:
                pass
        else:
            for repo in self._repositories.values():
                try:
                    package = repo.package(name, version, extras=extras)
                except PackageNotFound:
                    continue

                if package:
                    self._packages.append(package)

                    return package

        raise PackageNotFound("Package {} ({}) not found.".format(name, version))

    def find_packages(
        self,
        name,
        constraint=None,
        extras=None,
        allow_prereleases=False,
        repository=None,
    ):
        if (
            repository is not None
            and repository not in self._repositories
            and not self._ignore_repository_names
        ):
            raise ValueError('Repository "{}" does not exist.'.format(repository))

        if repository is not None and not self._ignore_repository_names:
            return self._repositories[repository].find_packages(
                name, constraint, extras=extras, allow_prereleases=allow_prereleases
            )

        packages = []
        for repo in self._repositories.values():
            packages += repo.find_packages(
                name, constraint, extras=extras, allow_prereleases=allow_prereleases
            )

        return packages

    def search(self, query, mode=BaseRepository.SEARCH_FULLTEXT):
        from .legacy_repository import LegacyRepository

        results = []
        for repository in self._repositories.values():
            if isinstance(repository, LegacyRepository):
                continue

            results += repository.search(query, mode=mode)

        return results
