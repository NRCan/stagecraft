import json

from stagecraft.libs.views.schema import output
from stagecraft.apps.organisation.views import (
    NodeView, NodeTypeView)


def main():
    combined = output([
        ('node-type', NodeTypeView),
        ('node', NodeView),
    ])

    print json.dumps(combined, indent=2)


if __name__ == '__main__':
    main()
