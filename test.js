class XY {
    constructor(x, y, parent = null) {
        this.x = x;
        this.y = y;
        this.parent = parent;
    }
}

class AABB {
    constructor(center, halfW, halfH, isGameObj = false) {
        this._center = center;
        this.halfW = halfW;
        this.halfH = halfH;
        this.setSides();
        this.points = [];
        if (isGameObj) {
            this.points = this.getPoints();
        }
    }

    get center() {
        return this._center;
    }

    set center(newCenter) {
        this._center = newCenter;
        this.setSides();
    }

    containsPoint(p) {
        return (
            (p.x >= this.leftSide) &&
            (p.x <= this.rightSide) &&
            (p.y >= this.topSide) &&
            (p.y <= this.bottomSide)
        );
    }

    intersectsAABB(other) {
        return (
            (this.leftSide < other.rightSide) &&
            (this.rightSide > other.leftSide) &&
            (this.topSide < other.bottomSide) &&
            (this.bottomSide > other.topSide)
        );
    }

    toRect() {
        return [
            this.leftSide,
            this.topSide,
            this.halfW * 2,
            this.halfH * 2
        ];
    }

    setSides() {
        this.leftSide = this._center.x - this.halfW;
        this.rightSide = this._center.x + this.halfW;
        this.topSide = this._center.y - this.halfH;
        this.bottomSide = this._center.y + this.halfH;
    }

    getPoints() {
        return [
            new XY(this.leftSide, this.topSide, this),
            new XY(this.leftSide, this.bottomSide, this),
            new XY(this.rightSide, this.topSide, this),
            new XY(this.rightSide, this.bottomSide, this)
        ];
    }
}


class QuadTree {
    static QT_NODE_CAPACITY = 1;

    constructor(boundary) {
        this.boundary = boundary;
        this.points = [];
        this.northWest = null;
        this.northEast = null;
        this.southWest = null;
        this.southEast = null;
    }

    insert(p) {
        if (!this.boundary.containsPoint(p) || !this.boundary.intersectsAABB(p.parent)) {
            return false;
        }

        if (this.points.length < QuadTree.QT_NODE_CAPACITY && this.northWest === null) {
            this.points.push(p);
            return true;
        }

        if (this.northWest === null) {
            this.subdivide();
        }

        if (this.northWest.insert(p)) return true;
        if (this.northEast.insert(p)) return true;
        if (this.southWest.insert(p)) return true;
        if (this.southEast.insert(p)) return true;

        return false;
    }

    subdivide() {
        const halfW = this.boundary.halfW / 2;
        const halfH = this.boundary.halfH / 2;
        this.northWest = new QuadTree(
            new AABB(
                new XY(
                    this.boundary.center.x - halfW,
                    this.boundary.center.y - halfH
                ),
                halfW, halfH
            )
        );
        this.northEast = new QuadTree(
            new AABB(
                new XY(
                    this.boundary.center.x + halfW,
                    this.boundary.center.y - halfH
                ),
                halfW, halfH
            )
        );
        this.southWest = new QuadTree(
            new AABB(
                new XY(
                    this.boundary.center.x - halfW,
                    this.boundary.center.y + halfH
                ),
                halfW, halfH
            )
        );
        this.southEast = new QuadTree(
            new AABB(
                new XY(
                    this.boundary.center.x + halfW,
                    this.boundary.center.y + halfH
                ),
                halfW, halfH
            )
        );
    }

    queryRange(range) {
        const pointsInRange = [];
        if (!this.boundary.intersectsAABB(range)) return pointsInRange;

        for (const p of this.points) {
            if (range.containsPoint(p) || range.intersectsAABB(p.parent)) {
                pointsInRange.push(p);
            }
        }

        if (this.northWest === null) return pointsInRange;

        pointsInRange.push(...this.northWest.queryRange(range));
        pointsInRange.push(...this.northEast.queryRange(range));
        pointsInRange.push(...this.southWest.queryRange(range));
        pointsInRange.push(...this.southEast.queryRange(range));

        return pointsInRange;
    }

    clear() {
        this.points.splice(0, this.points.length);

        if (this.northWest !== null) {
            this.northWest.clear();
            this.northWest = null;
        }

        if (this.northEast !== null) {
            this.northEast.clear();
            this.northEast = null;
        }

        if (this.southWest !== null) {
            this.southWest.clear();
            this.southWest = null;
        }

        if (this.southEast !== null) {
            this.southEast.clear();
            this.southEast = null;
        }
    }
}

const randint = (a, b) => Math.floor(Math.random() * (b - a + 1)) + a;

const makeObjs = () => {
    return new Array(10).fill(0).map(_ => new AABB(
        new XY(randint(0, 500), randint(0, 500)),
        randint(2, 100),
        randint(2, 100),
        true
    ));
}

const quad = new QuadTree(
    new AABB(
        new XY(250, 250),
        250, 250
    )
);

const gameObjs = makeObjs();

const playerArea = new AABB(new XY(50, 50), 25, 25);

const drawTreeRects = (t) => {
    rect(...t.boundary.toRect());
    if (t.northWest !== null) {
        drawTreeRects(t.northWest);
    }
    if (t.northEast !== null) {
        drawTreeRects(t.northEast);
    }
    if (t.southWest !== null) {
        drawTreeRects(t.southWest);
    }
    if (t.southEast !== null) {
        drawTreeRects(t.southEast);
    }
}

function setup() {
    createCanvas(500, 500);
}

function draw() {
    background(0);
    playerArea.center = new XY(mouseX, mouseY);
    quad.clear();
    for (const o of gameObjs) {
        for (const p of o.points) {
            quad.insert(p);
        }
    }
    stroke(255, 0, 0);
    strokeWeight(1);
    noFill();
    drawTreeRects(quad);
    stroke(255);
    for (const i of gameObjs) {
        rect(...i.toRect());
    }
    let inRange = quad.queryRange(playerArea);
    const ranegSet = new Set(inRange);
    let drawRect = new Set();
    for (const i of inRange) {
        if (!drawRect.has(i.parent)) {
            drawRect.add(i.parent);
            if (ranegSet.has(i)) {
                stroke(0, 255, 0);
                fill(0, 255, 0);
                rect(...i.parent.toRect());
            } else {
                stroke(255);
                fill(255);
                rect(...i.parent.toRect());
            }
        }
    }
    stroke(0, 0, 255);
    fill(0, 0, 255);
    rect(...playerArea.toRect());
}
