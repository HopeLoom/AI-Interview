import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Plus, Search, Filter, Eye, Edit, Trash2, User, Briefcase, Calendar, MapPin, Target, BookOpen, Play, History, Settings, KeyRound } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { useCompanyCandidate } from '@/contexts/CompanyCandidateContext';
import { useLocation } from 'wouter';
import { Navigation } from '@/components/ui/Navigation';
import { CandidateService, PracticeSession, Skill } from '@/services/candidateService';
import { JoinByCodeDialog } from '@/components/interview/JoinByCodeDialog';

const CandidateDashboard: React.FC = () => {
  const { toast } = useToast();
  const { user, updateProfile } = useCompanyCandidate();
  const [, setLocation] = useLocation();
  const [activeTab, setActiveTab] = useState('overview');
  const [showProfileEdit, setShowProfileEdit] = useState(false);
  const [showSkillEdit, setShowSkillEdit] = useState(false);
  const [showJoinByCodeDialog, setShowJoinByCodeDialog] = useState(false);
  
  const [practiceSessions, setPracticeSessions] = useState<PracticeSession[]>([]);
  const [skills, setSkills] = useState<Skill[]>([]);

  const [profileForm, setProfileForm] = useState({
    name: user?.name || '',
    email: user?.email || '',
    phone: '',
    location: '',
    linkedinUrl: '',
    githubUrl: '',
    portfolioUrl: ''
  });

  const [skillForm, setSkillForm] = useState({
    name: '',
    level: 'beginner' as const,
    category: 'technical' as const
  });

  useEffect(() => {
    if (user) {
      setProfileForm({
        name: user.name,
        email: user.email,
        phone: user.candidateDetails.phone || '',
        location: user.candidateDetails.location || '',
        linkedinUrl: user.candidateDetails.linkedinUrl || '',
        githubUrl: user.candidateDetails.githubUrl || '',
        portfolioUrl: user.candidateDetails.portfolioUrl || ''
      });

      // Load practice sessions and skills from service
      const loadData = async () => {
        try {
          const [sessions, userSkills] = await Promise.all([
            CandidateService.getPracticeSessions(user.id),
            CandidateService.getSkills(user.id)
          ]);
          const normalizedSessions = sessions.map((session) => ({
            ...session,
            completedAt: session.completedAt ? new Date(session.completedAt) : session.completedAt
          }));
          setPracticeSessions(normalizedSessions);
          setSkills(userSkills);
        } catch (error) {
          console.error('Failed to load candidate data:', error);
          toast({
            title: "Error",
            description: "Failed to load your data. Please try again.",
            variant: "destructive"
          });
        }
      };

      loadData();
    }
  }, [user, toast]);

  const handleProfileUpdate = async () => {
    if (user) {
      try {
        await CandidateService.updateProfile(user.id, {
          name: profileForm.name,
          email: profileForm.email,
          phone: profileForm.phone,
          location: profileForm.location,
          linkedin_url: profileForm.linkedinUrl,
          github_url: profileForm.githubUrl,
          portfolio_url: profileForm.portfolioUrl
        });

        updateProfile({
          name: profileForm.name,
          candidateDetails: {
            ...user.candidateDetails,
            phone: profileForm.phone,
            location: profileForm.location,
            linkedinUrl: profileForm.linkedinUrl,
            githubUrl: profileForm.githubUrl,
            portfolioUrl: profileForm.portfolioUrl
          }
        });
        
        toast({
          title: "Profile Updated",
          description: "Your profile has been updated successfully",
        });
        setShowProfileEdit(false);
      } catch (error) {
        console.error('Failed to update profile:', error);
        toast({
          title: "Update Failed",
          description: "We couldn't update your profile. Please try again.",
          variant: "destructive"
        });
      }
    }
  };

  const handleAddSkill = () => {
    if (skillForm.name.trim()) {
      setSkills([...skills, { ...skillForm, name: skillForm.name.trim() }]);
      setSkillForm({ name: '', level: 'beginner', category: 'technical' });
      setShowSkillEdit(false);
      
      toast({
        title: "Skill Added",
        description: `${skillForm.name} has been added to your skills`,
      });
    }
  };

  const startNewPractice = () => {
    setLocation('/configure');
  };

  const continuePractice = (sessionId: string) => {
    // Navigate to practice session
    setLocation(`/practice/${sessionId}`);
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'beginner': return 'bg-green-100 text-green-800';
      case 'intermediate': return 'bg-yellow-100 text-yellow-800';
      case 'advanced': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800';
      case 'in-progress': return 'bg-blue-100 text-blue-800';
      case 'scheduled': return 'bg-purple-100 text-purple-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (!user || user.userType !== 'candidate') {
    return <div>Access denied</div>;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />
      <div className="max-w-7xl mx-auto p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Welcome back, {user.name}! 👋</h1>
            <p className="text-gray-600 mt-2">Ready to ace your next interview? Let's practice!</p>
          </div>
          <div className="flex gap-3">
            <Button onClick={startNewPractice} className="bg-blue-600 hover:bg-blue-700">
              <Plus className="w-4 h-4 mr-2" />
              Start New Practice
            </Button>
            <Button
              onClick={() => setShowJoinByCodeDialog(true)}
              className="bg-blue-600 hover:bg-blue-700 text-white"
            >
              <KeyRound className="w-4 h-4 mr-2" />
              Join Interview by Code
            </Button>
            <Button variant="outline" onClick={() => setShowProfileEdit(true)}>
              <Settings className="w-4 h-4 mr-2" />
              Edit Profile
            </Button>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <Play className="h-6 w-6 text-blue-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Total Sessions</p>
                  <p className="text-2xl font-bold text-gray-900">{practiceSessions.length}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center">
                <div className="p-2 bg-green-100 rounded-lg">
                  <Target className="h-6 w-6 text-green-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Completed</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {practiceSessions.filter(s => s.status === 'completed').length}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center">
                <div className="p-2 bg-yellow-100 rounded-lg">
                  <BookOpen className="h-6 w-6 text-yellow-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Skills</p>
                  <p className="text-2xl font-bold text-gray-900">{skills.length}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <History className="h-6 w-6 text-purple-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Avg Score</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {practiceSessions.filter(s => s.score).length > 0 
                      ? Math.round(practiceSessions.filter(s => s.score).reduce((acc, s) => acc + (s.score || 0), 0) / practiceSessions.filter(s => s.score).length)
                      : 'N/A'
                    }
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Main Content Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="practice">Practice Sessions</TabsTrigger>
            <TabsTrigger value="skills">Skills</TabsTrigger>
            <TabsTrigger value="profile">Profile</TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Recent Practice Sessions */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <History className="h-5 w-5" />
                    Recent Practice Sessions
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {practiceSessions.slice(0, 3).map((session) => (
                      <div key={session.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <div>
                          <p className="font-medium text-gray-900">{session.title}</p>
                          <div className="flex items-center gap-2 mt-1">
                            <Badge className={getDifficultyColor(session.difficulty)}>
                              {session.difficulty}
                            </Badge>
                            <Badge className={getStatusColor(session.status)}>
                              {session.status}
                            </Badge>
                          </div>
                        </div>
                        {session.status === 'in-progress' && (
                          <Button size="sm" onClick={() => continuePractice(session.id)}>
                            Continue
                          </Button>
                        )}
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Skills Overview */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <BookOpen className="h-5 w-5" />
                    Skills Overview
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {skills.slice(0, 5).map((skill, index) => (
                      <div key={index} className="flex items-center justify-between">
                        <span className="font-medium text-gray-900">{skill.name}</span>
                        <Badge className={getDifficultyColor(skill.level)}>
                          {skill.level}
                        </Badge>
                      </div>
                    ))}
                  </div>
                  <Button 
                    variant="outline" 
                    className="w-full mt-4"
                    onClick={() => setShowSkillEdit(true)}
                  >
                    <Plus className="w-4 h-4 mr-2" />
                    Add Skill
                  </Button>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Practice Sessions Tab */}
          <TabsContent value="practice" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Practice Sessions</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {practiceSessions.map((session) => (
                    <div key={session.id} className="border rounded-lg p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <h3 className="font-semibold text-lg">{session.title}</h3>
                          <p className="text-gray-600">{session.role}</p>
                          <div className="flex items-center gap-2 mt-2">
                            <Badge className={getDifficultyColor(session.difficulty)}>
                              {session.difficulty}
                            </Badge>
                            <Badge className={getStatusColor(session.status)}>
                              {session.status}
                            </Badge>
                            <span className="text-sm text-gray-500">
                              {session.duration} min
                            </span>
                          </div>
                          {session.score && (
                            <p className="text-sm text-gray-600 mt-1">
                              Score: <span className="font-medium">{session.score}/100</span>
                            </p>
                          )}
                        </div>
                        <div className="flex gap-2">
                          {session.status === 'in-progress' && (
                            <Button onClick={() => continuePractice(session.id)}>
                              Continue
                            </Button>
                          )}
                          {session.status === 'completed' && (
                            <Button variant="outline">
                              <Eye className="w-4 h-4 mr-2" />
                              View Results
                            </Button>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Skills Tab */}
          <TabsContent value="skills" className="space-y-6">
            <Card>
              <CardHeader className="flex items-center justify-between">
                <CardTitle>Skills & Expertise</CardTitle>
                <Button onClick={() => setShowSkillEdit(true)}>
                  <Plus className="w-4 h-4 mr-2" />
                  Add Skill
                </Button>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {skills.map((skill, index) => (
                    <div key={index} className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="font-semibold">{skill.name}</h3>
                        <Badge className={getDifficultyColor(skill.level)}>
                          {skill.level}
                        </Badge>
                      </div>
                      <p className="text-sm text-gray-600 capitalize">{skill.category}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Profile Tab */}
          <TabsContent value="profile" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Profile Information</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label>Name</Label>
                    <p className="text-gray-900 font-medium">{user.name}</p>
                  </div>
                  <div>
                    <Label>Email</Label>
                    <p className="text-gray-900 font-medium">{user.email}</p>
                  </div>
                  <div>
                    <Label>Phone</Label>
                    <p className="text-gray-900 font-medium">
                      {user.candidateDetails.phone || 'Not provided'}
                    </p>
                  </div>
                  <div>
                    <Label>Location</Label>
                    <p className="text-gray-900 font-medium">
                      {user.candidateDetails.location || 'Not provided'}
                    </p>
                  </div>
                  <div>
                    <Label>LinkedIn</Label>
                    <p className="text-gray-900 font-medium">
                      {user.candidateDetails.linkedinUrl ? (
                        <a href={user.candidateDetails.linkedinUrl} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                          View Profile
                        </a>
                      ) : 'Not provided'}
                    </p>
                  </div>
                  <div>
                    <Label>GitHub</Label>
                    <p className="text-gray-900 font-medium">
                      {user.candidateDetails.githubUrl ? (
                        <a href={user.candidateDetails.githubUrl} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                          View Profile
                        </a>
                      ) : 'Not provided'}
                    </p>
                  </div>
                </div>
                <Button 
                  variant="outline" 
                  className="mt-4"
                  onClick={() => setShowProfileEdit(true)}
                >
                  <Edit className="w-4 h-4 mr-2" />
                  Edit Profile
                </Button>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>

      {/* Profile Edit Dialog */}
      <Dialog open={showProfileEdit} onOpenChange={setShowProfileEdit}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Edit Profile</DialogTitle>
          </DialogHeader>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label htmlFor="name">Name</Label>
              <Input
                id="name"
                value={profileForm.name}
                onChange={(e) => setProfileForm({ ...profileForm, name: e.target.value })}
              />
            </div>
            <div>
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                value={profileForm.email}
                onChange={(e) => setProfileForm({ ...profileForm, email: e.target.value })}
              />
            </div>
            <div>
              <Label htmlFor="phone">Phone</Label>
              <Input
                id="phone"
                value={profileForm.phone}
                onChange={(e) => setProfileForm({ ...profileForm, phone: e.target.value })}
              />
            </div>
            <div>
              <Label htmlFor="location">Location</Label>
              <Input
                id="location"
                value={profileForm.location}
                onChange={(e) => setProfileForm({ ...profileForm, location: e.target.value })}
              />
            </div>
            <div>
              <Label htmlFor="linkedin">LinkedIn URL</Label>
              <Input
                id="linkedin"
                value={profileForm.linkedinUrl}
                onChange={(e) => setProfileForm({ ...profileForm, linkedinUrl: e.target.value })}
              />
            </div>
            <div>
              <Label htmlFor="github">GitHub URL</Label>
              <Input
                id="github"
                value={profileForm.githubUrl}
                onChange={(e) => setProfileForm({ ...profileForm, githubUrl: e.target.value })}
              />
            </div>
            <div className="md:col-span-2">
              <Label htmlFor="portfolio">Portfolio URL</Label>
              <Input
                id="portfolio"
                value={profileForm.portfolioUrl}
                onChange={(e) => setProfileForm({ ...profileForm, portfolioUrl: e.target.value })}
              />
            </div>
          </div>
          <div className="flex justify-end gap-2 mt-6">
            <Button variant="outline" onClick={() => setShowProfileEdit(false)}>
              Cancel
            </Button>
            <Button onClick={handleProfileUpdate}>
              Save Changes
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Add Skill Dialog */}
      <Dialog open={showSkillEdit} onOpenChange={setShowSkillEdit}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add New Skill</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="skillName">Skill Name</Label>
              <Input
                id="skillName"
                value={skillForm.name}
                onChange={(e) => setSkillForm({ ...skillForm, name: e.target.value })}
                placeholder="e.g., React, Python, Communication"
              />
            </div>
            <div>
              <Label htmlFor="skillLevel">Proficiency Level</Label>
              <Select value={skillForm.level} onValueChange={(value: any) => setSkillForm({ ...skillForm, level: value })}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="beginner">Beginner</SelectItem>
                  <SelectItem value="intermediate">Intermediate</SelectItem>
                  <SelectItem value="advanced">Advanced</SelectItem>
                  <SelectItem value="expert">Expert</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="skillCategory">Category</Label>
              <Select value={skillForm.category} onValueChange={(value: any) => setSkillForm({ ...skillForm, category: value })}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="technical">Technical</SelectItem>
                  <SelectItem value="soft-skills">Soft Skills</SelectItem>
                  <SelectItem value="domain">Domain Knowledge</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="flex justify-end gap-2 mt-6">
            <Button variant="outline" onClick={() => setShowSkillEdit(false)}>
              Cancel
            </Button>
            <Button onClick={handleAddSkill}>
              Add Skill
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Join by Code Dialog */}
      <JoinByCodeDialog
        open={showJoinByCodeDialog}
        onOpenChange={setShowJoinByCodeDialog}
      />
    </div>
  );
};

export default CandidateDashboard;
