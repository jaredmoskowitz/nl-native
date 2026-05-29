// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "NotesFeature",
    platforms: [.macOS(.v13)],
    products: [
        .library(name: "NotesFeature", targets: ["NotesFeature"]),
    ],
    targets: [
        .target(name: "NotesFeature"),
        .testTarget(
            name: "NotesFeatureOracleTests",
            dependencies: ["NotesFeature"]
        ),
    ]
)
