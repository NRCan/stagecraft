# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'Node.lft'
        db.delete_column(u'organisation_node', u'lft')

        # Deleting field 'Node.parent'
        db.delete_column(u'organisation_node', 'parent_id')

        # Deleting field 'Node.level'
        db.delete_column(u'organisation_node', u'level')

        # Deleting field 'Node.tree_id'
        db.delete_column(u'organisation_node', u'tree_id')

        # Deleting field 'Node.rght'
        db.delete_column(u'organisation_node', u'rght')

        # Adding M2M table for field parents on 'Node'
        m2m_table_name = db.shorten_name(u'organisation_node_parents')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('from_node', models.ForeignKey(orm[u'organisation.node'], null=False)),
            ('to_node', models.ForeignKey(orm[u'organisation.node'], null=False))
        ))
        db.create_unique(m2m_table_name, ['from_node_id', 'to_node_id'])


    def backwards(self, orm):

        # User chose to not deal with backwards NULL issues for 'Node.lft'
        raise RuntimeError("Cannot reverse this migration. 'Node.lft' and its values cannot be restored.")
        
        # The following code is provided here to aid in writing a correct migration        # Adding field 'Node.lft'
        db.add_column(u'organisation_node', u'lft',
                      self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True),
                      keep_default=False)

        # Adding field 'Node.parent'
        db.add_column(u'organisation_node', 'parent',
                      self.gf('mptt.fields.TreeForeignKey')(related_name='children', null=True, to=orm['organisation.Node'], blank=True),
                      keep_default=False)


        # User chose to not deal with backwards NULL issues for 'Node.level'
        raise RuntimeError("Cannot reverse this migration. 'Node.level' and its values cannot be restored.")
        
        # The following code is provided here to aid in writing a correct migration        # Adding field 'Node.level'
        db.add_column(u'organisation_node', u'level',
                      self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True),
                      keep_default=False)


        # User chose to not deal with backwards NULL issues for 'Node.tree_id'
        raise RuntimeError("Cannot reverse this migration. 'Node.tree_id' and its values cannot be restored.")
        
        # The following code is provided here to aid in writing a correct migration        # Adding field 'Node.tree_id'
        db.add_column(u'organisation_node', u'tree_id',
                      self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True),
                      keep_default=False)


        # User chose to not deal with backwards NULL issues for 'Node.rght'
        raise RuntimeError("Cannot reverse this migration. 'Node.rght' and its values cannot be restored.")
        
        # The following code is provided here to aid in writing a correct migration        # Adding field 'Node.rght'
        db.add_column(u'organisation_node', u'rght',
                      self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True),
                      keep_default=False)

        # Removing M2M table for field parents on 'Node'
        db.delete_table(db.shorten_name(u'organisation_node_parents'))


    models = {
        u'organisation.node': {
            'Meta': {'object_name': 'Node'},
            'abbreviation': ('django.db.models.fields.CharField', [], {'max_length': '50', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '256'}),
            'parents': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['organisation.Node']", 'symmetrical': 'False'}),
            'typeOf': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['organisation.NodeType']"})
        },
        u'organisation.nodetype': {
            'Meta': {'object_name': 'NodeType'},
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '256'})
        }
    }

    complete_apps = ['organisation']