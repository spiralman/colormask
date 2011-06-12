//
//  ColorDistance.m
//  MaskingPlugins
//
//  Created by Thomas Stephens on 6/11/11.
//  Copyright 2011 __MyCompanyName__. All rights reserved.
//

#import "MaskingFilters.h"
#import <Foundation/Foundation.h>
#import <ApplicationServices/ApplicationServices.h>

@implementation ColorDistance

static CIKernel *_ColorDistanceKernel = nil;

- (id)init
{
    if(_ColorDistanceKernel == nil)
    {
		NSBundle    *bundle = [NSBundle bundleForClass:NSClassFromString(@"ColorDistance")];
		NSStringEncoding encoding = NSUTF8StringEncoding;
		NSError     *error = nil;
		NSString    *code = [NSString stringWithContentsOfFile:[bundle pathForResource:@"ColorDistance" ofType:@"cikernel"] encoding:encoding error:&error];
		NSArray     *kernels = [CIKernel kernelsWithString:code];
        
		_ColorDistanceKernel = [[kernels objectAtIndex:0] retain];
    }
    return [super init];
}


- (NSDictionary *)customAttributes
{
    return [NSDictionary dictionaryWithObjectsAndKeys:
            [NSDictionary dictionaryWithObjectsAndKeys:
             [CIColor colorWithRed:1.0 green:0.0 blue:0.0], kCIAttributeDefault,
             nil], @"inputColor",
            
            [NSDictionary dictionaryWithObjectsAndKeys:
             [NSNumber numberWithDouble: 0.00], kCIAttributeMin,
             [NSNumber numberWithDouble: 1.00], kCIAttributeMax,
             [NSNumber numberWithDouble: 0.40], kCIAttributeDefault,
             kCIAttributeTypeScalar,            kCIAttributeType,
             nil],                               @"inputChromaTolerance",
            
            [NSDictionary dictionaryWithObjectsAndKeys:
             [NSNumber numberWithDouble: 0.000001], kCIAttributeMin,
             [NSNumber numberWithDouble: 1.00], kCIAttributeMax,
             [NSNumber numberWithDouble: 1.0], kCIAttributeDefault,
             kCIAttributeTypeScalar,            kCIAttributeType,
             nil],                               @"inputFalloff",
            
            nil];
}

// called when setting up for fragment program and also calls fragment program
- (CIImage *)outputImage
{
    CISampler *src;
    
    src = [CISampler samplerWithImage:inputImage];
    
    return [self apply:_ColorDistanceKernel, src, inputColor, inputChromaTolerance, inputFalloff, kCIApplyOptionDefinition, [src definition], nil];
}

@end

@implementation LuminanceDistance

static CIKernel *_LuminanceDistanceKernel = nil;

- (id)init
{
    if(_LuminanceDistanceKernel == nil)
    {
		NSBundle    *bundle = [NSBundle bundleForClass:NSClassFromString(@"LuminanceDistance")];
		NSStringEncoding encoding = NSUTF8StringEncoding;
		NSError     *error = nil;
		NSString    *code = [NSString stringWithContentsOfFile:[bundle pathForResource:@"LuminanceDistance" ofType:@"cikernel"] encoding:encoding error:&error];
		NSArray     *kernels = [CIKernel kernelsWithString:code];
        
		_LuminanceDistanceKernel = [[kernels objectAtIndex:0] retain];
    }
    return [super init];
}


- (NSDictionary *)customAttributes
{
    return [NSDictionary dictionaryWithObjectsAndKeys:
            [NSDictionary dictionaryWithObjectsAndKeys:
             [NSNumber numberWithDouble: 0.00], kCIAttributeMin,
             [NSNumber numberWithDouble: 1.00], kCIAttributeMax,
             [NSNumber numberWithDouble: 0.40], kCIAttributeDefault,
             kCIAttributeTypeScalar,            kCIAttributeType,
             nil],                               @"inputLuminanceTolerance",
            
            [NSDictionary dictionaryWithObjectsAndKeys:
             [NSNumber numberWithDouble: 0.000001], kCIAttributeMin,
             [NSNumber numberWithDouble: 1.00], kCIAttributeMax,
             [NSNumber numberWithDouble: 1.0], kCIAttributeDefault,
             kCIAttributeTypeScalar,            kCIAttributeType,
             nil],                               @"inputFalloff",
            
            nil];
}

// called when setting up for fragment program and also calls fragment program
- (CIImage *)outputImage
{
    CISampler *src;
    
    src = [CISampler samplerWithImage:inputImage];
    
    return [self apply:_LuminanceDistanceKernel, src, inputLuminanceTolerance, inputFalloff, kCIApplyOptionDefinition, [src definition], nil];
}

@end

@implementation PerceptualDistance

static CIKernel *_PerceptualDistanceKernel = nil;

- (id)init
{
    if(_PerceptualDistanceKernel == nil)
    {
		NSBundle    *bundle = [NSBundle bundleForClass:NSClassFromString(@"PerceptualDistance")];
		NSStringEncoding encoding = NSUTF8StringEncoding;
		NSError     *error = nil;
		NSString    *code = [NSString stringWithContentsOfFile:[bundle pathForResource:@"PerceptualDistance" ofType:@"cikernel"] encoding:encoding error:&error];
		NSArray     *kernels = [CIKernel kernelsWithString:code];
        
		_PerceptualDistanceKernel = [[kernels objectAtIndex:0] retain];
    }
    return [super init];
}


- (NSDictionary *)customAttributes
{
    return [NSDictionary dictionaryWithObjectsAndKeys:
            [NSDictionary dictionaryWithObjectsAndKeys:
             [CIColor colorWithRed:1.0 green:0.0 blue:0.0], kCIAttributeDefault,
             nil], @"inputColor",
            
            [NSDictionary dictionaryWithObjectsAndKeys:
             [NSNumber numberWithDouble: 0.00], kCIAttributeMin,
             [NSNumber numberWithDouble: 1.00], kCIAttributeMax,
             [NSNumber numberWithDouble: 0.40], kCIAttributeDefault,
             kCIAttributeTypeScalar,            kCIAttributeType,
             nil],                               @"inputChromaTolerance",
            
            [NSDictionary dictionaryWithObjectsAndKeys:
             [NSNumber numberWithDouble: 0.00], kCIAttributeMin,
             [NSNumber numberWithDouble: 1.00], kCIAttributeMax,
             [NSNumber numberWithDouble: 0.40], kCIAttributeDefault,
             kCIAttributeTypeScalar,            kCIAttributeType,
             nil],                               @"inputLuminanceTolerance",
            
            [NSDictionary dictionaryWithObjectsAndKeys:
             [NSNumber numberWithDouble: 0.000001], kCIAttributeMin,
             [NSNumber numberWithDouble: 1.00], kCIAttributeMax,
             [NSNumber numberWithDouble: 1.0], kCIAttributeDefault,
             kCIAttributeTypeScalar,            kCIAttributeType,
             nil],                               @"inputFalloff",
            
            nil];
}

// called when setting up for fragment program and also calls fragment program
- (CIImage *)outputImage
{
    CISampler *src;
    
    src = [CISampler samplerWithImage:inputImage];
    
    return [self apply:_PerceptualDistanceKernel, src, inputColor, inputChromaTolerance, inputLuminanceTolerance, inputFalloff, kCIApplyOptionDefinition, [src definition], nil];
}

@end
