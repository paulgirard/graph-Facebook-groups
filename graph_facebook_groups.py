#!/usr/bin/python
# -*- coding: utf-8 -*-
######
#
#   graph facebook groups based on the common members
#   main developper : Paul Girard, médialab Sciences Po
#	repository : http://github.com/paulgirard/graph_group_facebook
#
#	licence : GPL v3
#
#	depedencies :
#
#		PyGexf lib : 
#		$easy_install pygexf
#		repository : http://github.com/paulgirard/pygexf
#	    documentation : http://packages.python.org/pygexf
#
#		Facebook API python lib : 
#		https://github.com/facebook/python-sdk
#
#		Facebook token : 
#		get a facebook app token : http://developers.facebook.com/docs/authentication/
#		the token should be in a file ./token
#
#		groups file : groups.csv
#		write the id, name and number of members of group to graph in a TSV (Tab Separated Values) file named groups.csv
#		id	name	nb members
#
#	usage :
#
#		python graph_group_facebook.py 
#
#	output : 
#		groups.gexf
#
#		a group to group weighted graph 
#		groups are linked by the amount of common numbers
#
#		groups_members.gexf
#
#		a group to member bi-partite graph
#		members are linked to groups they belong to
#
#   Respect privacy ! 
# 		Watch out what you're doing with private life data !
#		Please comply with your country legislation regarding privacy.
#		The graph you are about to make with this lib should be anonymised before any publication.
#
######

from  itertools import combinations
import random
import facebook
import gexf
import codecs

class Group_facebook(list) :
	# a group is a list of members object plus an id
	
	def __init__(self,id,name="",nb_members=-1) :
		self.id=id
		self.name=name
		self.nb_members=nb_members

class Groups_links(dict):
	
	def add(self,id1,id2,member_id) :
		try :
			self[id1+"_"+id2].append(member_id)
		except KeyError:
			self[id1+"_"+id2]=[member_id]
		return self[id1+"_"+id2]
	
	def get_gexf_groupsonly(self,groups,author="",title=""):
		g=gexf.Gexf(author,title)
		graph=g.addGraph("undirected","static","groups")
		nb_members_att=graph.addNodeAttribute("nb_members","0")
		
		# add nodes
		for group in groups.values() :

			graph.addNode(group.id,group.name).addAttribute(nb_members_att,str(group.nb_members))
		
		for (k,v) in self.iteritems() :
			(id1,id2)=k.split("_")
			# add edge
			graph.addEdge(k,id1,id2,str(len(v)))
		
		return g
			
	def get_gexf_groups_members(self,groups,members,author="",title=""):
		g=gexf.Gexf(author,title)
		graph=g.addGraph("undirected","static","groups members")
		nb_members_att=graph.addNodeAttribute("nb_members","1")
		type_att=graph.addNodeAttribute("type","group","String")
		
		
		# add nodes
		for group in groups.values() :
			n=graph.addNode("group_"+group.id,group.name)
			n.addAttribute(nb_members_att,str(group.nb_members))
			n.addAttribute(type_att,"group")
		
		for member in members.values() :
			n=graph.addNode("member_"+member.id,member.name)
			n.addAttribute(type_att,"member")
		
			for group_id in member :
				graph.addEdge(group_id+"_"+member.id,"member_"+member.id,"group_"+group_id)
					
		return g
			
class Member_facebook(list) :

	# member list the group he belongs to
	def __init__(self,id,name) :
		self.id=id
		self.name=name
		
	
class Members_facebook(dict) :
	# all the members of all the groups as a dictionnary id:object


	def add(self,member_id,member_name,group_id):
			try :
				self[member_id].append(group_id)
			except KeyError:
				self[member_id]=Member_facebook(member_id,member_name)
				self[member_id].append(group_id)
	
	def process_groups_links(self) :
		self.groups_links=Groups_links()
		for (id,m) in self.iteritems() : 
			for (g1,g2) in combinations(m,2) :
				self.groups_links.add(g1,g2,id)
		return self.groups_links


groups={}
# load groups id
f=codecs.open("groups.csv","r","utf-8")
# dump column names
_ = f.readline()
for line in f :
	(name,id,nb_members)=line.split("\t")
	groups[id]=Group_facebook(id,name,int(nb_members))

print "# groups loaded"
for group in  groups.values() :
	print group.id+" "+group.name+" "+str(group.nb_members)

# load token
(_,token)=open("token").readline().split("=")
facebook_api=facebook.GraphAPI(token)

members=Members_facebook()
for group in groups.values() :
	try :
		# harvest data from Facebook
		print "harvesting group "+group.name+" "+group.id
		ms = facebook_api.get_connections(group.id, "members")
		# process users
		group.nb_members=len(ms['data'])
		for user in ms["data"] : 
	 
			#for membership in set([ groups.values()[random.randint(0,len(groups)-1)].id for _ in range(0,3)]) :
			members.add(user["id"],user["name"],group.id)
	except :
		print "# ERROR on group harvesting "+group.name+" "+group.id

#for group in  groups.values() :
#	print group.id+" "+group.name+" "+str(group.nb_members)
#
#for member in members.values() :
#	print member.name+" "+member.id
#	print [groups[g].name for g in member ]


gl=members.process_groups_links()
#print gl
g=gl.get_gexf_groupsonly(groups)
output_file=open("groups.gexf","w")
g.write(output_file)
output_file.close()

g=gl.get_gexf_groups_members(groups,members)
output_file=open("groups_members.gexf","w")
g.write(output_file)
output_file.close()
