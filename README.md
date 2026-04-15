## **Experimental** Swift Standard Library Package

This repository contains a mirror of the Swift standard library, separated from the Swift compiler sources and testsuite. It is currently an *experiment* in building the Swift standard library and friends for Embedded Swift (only) purely from sources, without relying on prebuilt binaries in the toolchain.

The only unique content in this repository are the scripts for performing the cloning itself. Any changes to the Swift standard library, its package, or supporting code must go to the [main Swift repository](https://github.com/swiftlang/swift/) and will be mirrored here.