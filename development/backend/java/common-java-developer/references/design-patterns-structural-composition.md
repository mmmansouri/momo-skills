# Structural Design Patterns — Composition & Sharing

> Patterns that build whole-part hierarchies and share state across many instances:
> Composite, Flyweight.
> Classic GoF forms paired with modern-Java idioms (sealed interfaces, records, `ConcurrentHashMap` factories).

---

## Table of Contents

1. [Composite Pattern](#composite-pattern)
2. [Flyweight Pattern](#flyweight-pattern)

---

## Composite Pattern

### 🟢 When to use
- Tree structures (file systems, org charts, UI components)
- Treat individual objects and compositions uniformly
- Recursive structures

```java
// Component - common interface
sealed interface FileSystemNode permits File, Directory {
    String getName();
    long getSize();
    void print(String indent);
}

// Leaf
record File(String name, long size) implements FileSystemNode {
    @Override
    public String getName() { return name; }

    @Override
    public long getSize() { return size; }

    @Override
    public void print(String indent) {
        System.out.println(indent + "📄 " + name + " (" + formatSize(size) + ")");
    }

    private String formatSize(long bytes) {
        if (bytes < 1024) return bytes + " B";
        if (bytes < 1024 * 1024) return bytes / 1024 + " KB";
        return bytes / (1024 * 1024) + " MB";
    }
}

// Composite
record Directory(String name, List<FileSystemNode> children) implements FileSystemNode {
    // Defensive copy in compact constructor
    public Directory {
        children = List.copyOf(children);
    }

    @Override
    public String getName() { return name; }

    @Override
    public long getSize() {
        return children.stream()
            .mapToLong(FileSystemNode::getSize)
            .sum();
    }

    @Override
    public void print(String indent) {
        System.out.println(indent + "📁 " + name + "/");
        children.forEach(child -> child.print(indent + "  "));
    }

    // Builder for mutable construction phase
    public static Builder builder(String name) {
        return new Builder(name);
    }

    public static class Builder {
        private final String name;
        private final List<FileSystemNode> children = new ArrayList<>();

        Builder(String name) { this.name = name; }

        public Builder addFile(String name, long size) {
            children.add(new File(name, size));
            return this;
        }

        public Builder addDirectory(Directory dir) {
            children.add(dir);
            return this;
        }

        public Directory build() {
            return new Directory(name, children);
        }
    }
}

// Usage
Directory root = Directory.builder("project")
    .addFile("README.md", 1024)
    .addFile("pom.xml", 2048)
    .addDirectory(
        Directory.builder("src")
            .addFile("Main.java", 4096)
            .addFile("Utils.java", 2048)
            .build()
    )
    .addDirectory(
        Directory.builder("test")
            .addFile("MainTest.java", 3072)
            .build()
    )
    .build();

root.print("");  // Prints tree structure
System.out.println("Total size: " + root.getSize());  // Recursive calculation

// Pattern matching with composite
long countJavaFiles(FileSystemNode node) {
    return switch (node) {
        case File(String name, _) when name.endsWith(".java") -> 1;
        case File _ -> 0;
        case Directory(_, List<FileSystemNode> children) ->
            children.stream().mapToLong(this::countJavaFiles).sum();
    };
}
```

---

## Flyweight Pattern

### 🟢 When to use
- Large number of similar objects
- Objects share significant common state
- Memory optimization is critical

```java
// Flyweight - immutable shared state (intrinsic)
record TreeType(String name, String color, String texture, byte[] meshData) {
    void draw(Graphics g, int x, int y) {
        // Use shared meshData to render at specific position (extrinsic state)
        g.drawTree(meshData, x, y, color);
    }
}

// Flyweight Factory
class TreeTypeFactory {
    private static final Map<String, TreeType> cache = new ConcurrentHashMap<>();

    public static TreeType getTreeType(String name, String color, String texture) {
        String key = name + "_" + color + "_" + texture;
        return cache.computeIfAbsent(key, k -> {
            byte[] meshData = loadMeshData(name);  // Expensive, done once
            return new TreeType(name, color, texture, meshData);
        });
    }

    private static byte[] loadMeshData(String name) {
        // Load 3D mesh data from file - expensive operation
        return new byte[100_000];  // Simulated heavy data
    }
}

// Context - contains extrinsic state (position)
record Tree(int x, int y, TreeType type) {
    void draw(Graphics g) {
        type.draw(g, x, y);  // Delegate to flyweight with position
    }
}

// Client - forest with millions of trees
class Forest {
    private final List<Tree> trees = new ArrayList<>();

    public void plantTree(int x, int y, String name, String color, String texture) {
        // Get shared flyweight - memory efficient!
        TreeType type = TreeTypeFactory.getTreeType(name, color, texture);
        trees.add(new Tree(x, y, type));
    }

    public void draw(Graphics g) {
        trees.forEach(tree -> tree.draw(g));
    }

    // Memory savings example:
    // 1,000,000 trees with 3 tree types
    // Without flyweight: 1,000,000 × 100KB = 100GB
    // With flyweight: 3 × 100KB + 1,000,000 × 12B = 300KB + 12MB ≈ 12MB
}

// Java's built-in flyweights
String s1 = "hello".intern();  // String pool
String s2 = "hello".intern();
assert s1 == s2;  // Same object

Integer i1 = Integer.valueOf(100);  // Integer cache (-128 to 127)
Integer i2 = Integer.valueOf(100);
assert i1 == i2;  // Same object
```
