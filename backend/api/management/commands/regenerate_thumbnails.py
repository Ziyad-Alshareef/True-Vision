from django.core.management.base import BaseCommand, CommandError
from api.models import Video
from django.db import transaction
import time

class Command(BaseCommand):
    help = 'Regenerates thumbnails for all videos or a specific video ID'

    def add_arguments(self, parser):
        parser.add_argument('--video_id', type=int, help='Specific video ID to regenerate thumbnail for')
        parser.add_argument('--force', action='store_true', help='Force regeneration even if thumbnail exists')
        
    def handle(self, *args, **options):
        video_id = options.get('video_id')
        force = options.get('force', False)
        
        if video_id:
            # Regenerate for specific video
            try:
                video = Video.objects.get(Video_id=video_id)
                self.regenerate_thumbnail(video, force)
            except Video.DoesNotExist:
                raise CommandError(f'Video with ID {video_id} does not exist')
        else:
            # Regenerate for all videos
            videos = Video.objects.all().order_by('-Uploaded_at')
            
            if not videos:
                self.stdout.write(self.style.WARNING('No videos found in the database.'))
                return
                
            self.stdout.write(f'Found {videos.count()} videos. Starting thumbnail regeneration...')
            
            success_count = 0
            failure_count = 0
            skipped_count = 0
            
            for i, video in enumerate(videos):
                self.stdout.write(f'Processing video {i+1}/{videos.count()} (ID: {video.Video_id})...')
                
                # Skip if thumbnail exists and force is False
                if video.Thumbnail and not force:
                    self.stdout.write(self.style.SUCCESS(f'  - Skipping video {video.Video_id}, thumbnail already exists'))
                    skipped_count += 1
                    continue
                
                result = self.regenerate_thumbnail(video, force)
                if result:
                    success_count += 1
                else:
                    failure_count += 1
                
                # Pause briefly to avoid overloading the system
                time.sleep(0.5)
            
            self.stdout.write(self.style.SUCCESS(f'Thumbnail regeneration complete:'))
            self.stdout.write(f'  - Successful: {success_count}')
            self.stdout.write(f'  - Failed: {failure_count}')
            self.stdout.write(f'  - Skipped: {skipped_count}')
            
    def regenerate_thumbnail(self, video, force=False):
        """Regenerate thumbnail for a specific video"""
        try:
            if video.Thumbnail and not force:
                self.stdout.write(f'Video {video.Video_id} already has a thumbnail. Use --force to regenerate.')
                return True
                
            self.stdout.write(f'Regenerating thumbnail for video {video.Video_id}...')
            
            # Clear existing thumbnail if force is True
            if video.Thumbnail and force:
                self.stdout.write('Clearing existing thumbnail...')
                video.Thumbnail = None
                video.save(update_fields=['Thumbnail'])
            
            # Generate new thumbnail
            with transaction.atomic():
                result = video.generate_thumbnail()
                video.save(update_fields=['Thumbnail'])
                
                if result:
                    self.stdout.write(self.style.SUCCESS(f'Successfully regenerated thumbnail for video {video.Video_id}'))
                    return True
                else:
                    self.stdout.write(self.style.WARNING(f'Generated placeholder for video {video.Video_id} (no valid frame found)'))
                    return False
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error regenerating thumbnail for video {video.Video_id}: {str(e)}'))
            return False 