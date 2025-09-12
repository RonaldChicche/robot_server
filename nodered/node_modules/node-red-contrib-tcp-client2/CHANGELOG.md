# Change Log

All notable changes to this project will be documented in this file. This project adheres to [Semantic Versioning](http://semver.org/).

## [unreleased]

### Added
### Changed
### Fixed

## [1.1.2]


### Added

### Changed
- Improved readme
- Improved help

### Fixed
- Improved fault handling and throwing errors [#3](https://github.com/jorgen-k/node-red-contrib-tcp-client2/issues/3)

## [1.1.1] - 2024-03-03

### Added
- Examples

### Changed
- Improved Readme for TCP-Client

### Fixed
- TCP Client: Checkbox not visible in gui
- TCP Client: Fixed error when sending objects.
- TCP CLient: Fixed error handling stream of strings.

## [1.1.0] - 2024-03-02
### Added
- New TCP server node
- Node status for TCP client
- Configurable timeout and retries for TCP Client
- Improved logging with loglevels setable att configuration
- Example flow
- Test flow

### Changed
- Improved documentation
- Improved fault handling
- Total rewrite of tcp client, more robust
- TCP-client: To connect the "connect" keyword shall be used. "listen" still supported but deprecated.
- TCP-client: Do not support connection pool. It did not work in legacy implementation. One tcp-client node supports one connection at a time. If more than one connection is needed, use one node per connection.

### Fixed
- Several bugs in gui
- Due to rewrite now thouroughly happy-tested, see (TESTING.md)

## [1.0.0] - 2024-02-28
### Added
- Initial release of the TCP client node.
- Ability to establish TCP connections with designated hosts.
- Support for dynamic management of connections using provided arguments.
- Feature to transmit data over TCP ports.

### Changed
- Replaced deprecated node-red-contrib-tcp-client by Tiago Costa.
- Removed support for xml translation due to separation of concern. (This 
should be a separate node)
- Removed support for the client to be a server. This might be implemented in a separate server node in the future. Also due to separation of concerns.

### Fixed
- Refactoring and simplification of code inspired from node-red-contrib-tcp-client, fixing closing issues and more.

